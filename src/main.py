"""
CLI del asistente «Consultor Normativo» — Avance 1 (ingeniería de prompts).

Ejemplos de uso
---------------
  python src/main.py
        Modo interactivo. Usa TODOS los fragmentos normativos como contexto.

  python src/main.py --normas ley_1581_2012 ley_1480_2011
        Modo interactivo acotando el contexto a normas específicas.

  python src/main.py --formato markdown
        Cambia el formato de salida (json | markdown).

  python src/main.py --demo
        Ejecuta una batería de consultas de ejemplo (útil para las capturas del PDF).

  python src/main.py --ver-prompt --normas ley_820_2003
        Imprime el prompt ensamblado (system + usuario) SIN llamar al modelo.
        Sirve para evidenciar la estructura de prompts aunque no haya modelo disponible.

  python src/main.py --modo documento --documento contrato.pdf
        Modo de análisis documental: carga un .txt/.pdf arbitrario (no normativa
        colombiana) y responde preguntas sobre él con el mismo criterio de
        cero-alucinación, citando el fragmento exacto que respalda cada respuesta.

Comandos dentro del modo interactivo (--modo normativo, por defecto)
----------------------------------------------------------------------
  /salir                        termina la sesión
  /normas a b c                 fija las normas activas en el contexto (sin args = todas)
  /formato json|markdown        cambia el formato de salida
  /ver-prompt                   muestra el prompt de la última consulta escrita

Comandos dentro del modo interactivo (--modo documento)
----------------------------------------------------------------------
  /salir                        termina la sesión
  /otro <ruta>                  cambia de documento (.txt o .pdf)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# En Windows la consola suele usar una codificación heredada (cp1252) que muestra
# mal las tildes y la "ñ". Forzamos UTF-8 en la salida para que las capturas del
# PDF de evidencias se vean correctamente.
for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# La consola clásica de Windows (cmd.exe) no interpreta secuencias ANSI a menos
# que se active el modo de terminal virtual; este truco lo activa sin librerías
# externas (PowerShell y Windows Terminal ya lo soportan de forma nativa).
if sys.platform == "win32":
    os.system("")

_RESET, _BOLD, _DIM = "\033[0m", "\033[1m", "\033[2m"
_CYAN, _GREEN, _YELLOW, _RED, _MAGENTA = (
    "\033[36m", "\033[32m", "\033[33m", "\033[31m", "\033[35m",
)
_COLOR_CONFIANZA = {"alto": _GREEN, "medio": _YELLOW, "bajo": _RED}

_JSON_TOKEN_RE = re.compile(
    r'(?P<key>"(?:\\.|[^"\\])*")(?=\s*:)'
    r'|(?P<string>"(?:\\.|[^"\\])*")'
    r'|(?P<bool_null>\btrue\b|\bfalse\b|\bnull\b)'
    r'|(?P<number>-?\d+(?:\.\d+)?)'
)


def _colorear_json(json_str: str) -> str:
    def _reemplazar(m: re.Match) -> str:
        if m.group("key"):
            return f"{_CYAN}{m.group('key')}{_RESET}"
        if m.group("string"):
            return f"{_GREEN}{m.group('string')}{_RESET}"
        if m.group("bool_null"):
            return f"{_YELLOW}{m.group('bool_null')}{_RESET}"
        return f"{_MAGENTA}{m.group('number')}{_RESET}"

    return _JSON_TOKEN_RE.sub(_reemplazar, json_str)


def _colorear_markdown(md: str) -> str:
    lineas = []
    for linea in md.splitlines():
        if linea.startswith("## "):
            linea = f"{_BOLD}{_CYAN}{linea}{_RESET}"
        elif linea.startswith(">"):
            linea = f"{_DIM}{linea}{_RESET}"
        lineas.append(linea)
    return "\n".join(lineas)

try:
    from dotenv import load_dotenv
except ImportError:  # el proyecto puede correr si las variables ya están en el entorno
    def load_dotenv(*_args, **_kwargs):
        return False

# Permite ejecutar el archivo directamente (python src/main.py) resolviendo
# los imports del paquete `prompts` y de los módulos hermanos.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from document_loader import leer_documento  # noqa: E402
from llm_client import ClienteLLM, ErrorLLM  # noqa: E402
from prompt_builder import (  # noqa: E402
    cargar_contexto,
    construir_prompt_documento,
    construir_prompt_usuario,
)
from prompts.system_prompt import (  # noqa: E402
    FORMATO_JSON,
    FORMATO_MARKDOWN,
    construir_system_prompt,
)
from prompts.system_prompt_documento import construir_system_prompt_documento  # noqa: E402

# (consulta, [normas de contexto] | None -> None significa "sin contexto")
CONSULTAS_DEMO = [
    (
        "Si quiero terminar mi contrato de arriendo antes de tiempo, ¿con cuánta "
        "anticipación debo avisar y tengo que pagar algo?",
        ["ley_820_2003"],
    ),
    (
        "¿Qué derechos tengo sobre mis datos personales y en cuánto tiempo debe "
        "responderme una empresa cuando le hago una consulta?",
        ["ley_1581_2012"],
    ),
    (
        "Compré un electrodoméstico por internet y me arrepentí al día siguiente. "
        "¿Puedo devolverlo y que me devuelvan la plata?",
        ["ley_1480_2011"],
    ),
    (
        "¿Cuál es la sanción por presentar una declaración tributaria después del plazo?",
        ["estatuto_tributario"],
    ),
    (
        "¿Qué requisitos debe cumplir una demanda para que el juez la admita?",
        ["codigo_general_proceso_ley_1564_2012"],
    ),
    (
        "¿Me recomiendas invertir en criptomonedas este mes?",
        None,  # fuera de alcance
    ),
    (
        "¿La ley colombiana permite el matrimonio entre primos hermanos?",
        ["codigo_civil"],  # el fragmento cargado no cubre matrimonio -> "no está en las fuentes"
    ),
]


def imprimir_respuesta(texto: str, formato: str) -> None:
    separador = f"{_DIM}{'─' * 60}{_RESET}"
    if formato == FORMATO_JSON:
        try:
            datos = json.loads(texto)
            confianza = str(datos.get("nivel_confianza", "")).lower()
            color_confianza = _COLOR_CONFIANZA.get(confianza, "")
            bonito = json.dumps(datos, ensure_ascii=False, indent=2)
            print(separador)
            print(_colorear_json(bonito))
            print(separador)
            if confianza:
                print(f"{_BOLD}Nivel de confianza:{_RESET} {color_confianza}{confianza}{_RESET}")
            return
        except json.JSONDecodeError:
            print("[aviso] la salida no es JSON válido; se muestra tal cual:\n")
            print(texto)
            return
    print(separador)
    print(_colorear_markdown(texto))
    print(separador)


def ejecutar_demo(cliente: ClienteLLM, formato: str) -> None:
    system_prompt = construir_system_prompt(formato)
    for i, (consulta, normas) in enumerate(CONSULTAS_DEMO, 1):
        contexto = (
            cargar_contexto(normas)
            if normas
            else "(No se cargó contexto normativo para esta consulta.)"
        )
        user_prompt = construir_prompt_usuario(consulta, contexto)
        print("=" * 80)
        print(f"CONSULTA {i}: {consulta}")
        print(f"NORMAS EN CONTEXTO: {', '.join(normas) if normas else '—'}")
        print("-" * 80)
        try:
            salida = cliente.generar(system_prompt, user_prompt, formato_json=(formato == FORMATO_JSON))
            imprimir_respuesta(salida, formato)
        except ErrorLLM as e:
            print(f"[ERROR] {e}")
        print()


def ejecutar_interactivo(cliente: ClienteLLM, formato: str, normas) -> None:
    print("=== Consultor Normativo (Avance 1) ===")
    print(f"Motor: {cliente.describir()}")
    print(f"Formato de salida: {formato}")
    print(f"Normas en contexto: {', '.join(normas) if normas else 'todas'}")
    print("Escriba su consulta. Comandos: /salir  /normas  /formato  /ver-prompt\n")

    ultima_consulta = None
    while True:
        try:
            entrada = input("Consulta> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            return
        if not entrada:
            continue

        if entrada.lower() in ("/salir", "/exit", "/quit"):
            print("Hasta luego.")
            return

        if entrada.lower().startswith("/formato"):
            partes = entrada.split()
            if len(partes) == 2 and partes[1] in (FORMATO_JSON, FORMATO_MARKDOWN):
                formato = partes[1]
                print(f"[ok] formato = {formato}\n")
            else:
                print("[uso] /formato json|markdown\n")
            continue

        if entrada.lower().startswith("/normas"):
            partes = entrada.split()
            normas = partes[1:] or None
            try:
                cargar_contexto(normas)  # valida que existan
                print(f"[ok] normas en contexto = {', '.join(normas) if normas else 'todas'}\n")
            except FileNotFoundError as e:
                print(f"[error] {e}\n")
                normas = None
            continue

        if entrada.lower() == "/ver-prompt":
            if not ultima_consulta:
                print("[info] escriba primero una consulta.\n")
                continue
            contexto = cargar_contexto(normas)
            print("\n----- SYSTEM PROMPT -----")
            print(construir_system_prompt(formato))
            print("\n----- USER PROMPT -----")
            print(construir_prompt_usuario(ultima_consulta, contexto))
            print("----- FIN -----\n")
            continue

        ultima_consulta = entrada
        contexto = cargar_contexto(normas)
        system_prompt = construir_system_prompt(formato)
        user_prompt = construir_prompt_usuario(entrada, contexto)
        try:
            salida = cliente.generar(
                system_prompt, user_prompt, formato_json=(formato == FORMATO_JSON)
            )
            print()
            imprimir_respuesta(salida, formato)
            print()
        except ErrorLLM as e:
            print(f"[ERROR] {e}\n")


def ejecutar_documento_interactivo(cliente: ClienteLLM, ruta_inicial: str) -> None:
    """Modo de análisis documental: carga un .txt/.pdf arbitrario y responde preguntas
    sobre él con criterio de cero-alucinación (ver prompts/system_prompt_documento.py).
    """
    print("=== Consultor Normativo — modo análisis documental ===")
    print(f"Motor: {cliente.describir()}")
    print("Comandos: /salir  /otro <ruta>\n")

    system_prompt = construir_system_prompt_documento()
    ruta = ruta_inicial
    documento_texto = None

    while True:
        if documento_texto is None:
            try:
                documento_texto = leer_documento(ruta)
                print(f"[ok] documento cargado: {ruta} ({len(documento_texto)} caracteres)\n")
            except (FileNotFoundError, ValueError) as e:
                print(f"[error] {e}\n")
                nueva_ruta = input("Ruta del documento (.txt o .pdf) > ").strip()
                if nueva_ruta.lower() in ("/salir", "salir"):
                    print("Hasta luego.")
                    return
                ruta = nueva_ruta
                continue

        try:
            entrada = input("Pregunta> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            return
        if not entrada:
            continue

        if entrada.lower() in ("/salir", "/exit", "/quit"):
            print("Hasta luego.")
            return

        if entrada.lower().startswith("/otro"):
            partes = entrada.split(maxsplit=1)
            if len(partes) != 2:
                print("[uso] /otro <ruta al archivo .txt o .pdf>\n")
                continue
            ruta = partes[1].strip()
            documento_texto = None
            continue

        user_prompt = construir_prompt_documento(entrada, documento_texto)
        try:
            salida = cliente.generar(system_prompt, user_prompt, formato_json=True)
            print()
            imprimir_respuesta(salida, FORMATO_JSON)
            print()
        except ErrorLLM as e:
            print(f"[ERROR] {e}\n")


def solo_ver_prompt(formato: str, normas, consulta: str) -> None:
    contexto = cargar_contexto(normas)
    print("----- SYSTEM PROMPT -----")
    print(construir_system_prompt(formato))
    print("\n----- USER PROMPT -----")
    print(construir_prompt_usuario(consulta, contexto))


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Consultor Normativo - Avance 1")
    parser.add_argument("--modo", choices=["normativo", "documento"], default="normativo",
                        help="'normativo' (por defecto): Consultor Normativo colombiano. "
                             "'documento': análisis de un .txt/.pdf arbitrario cargado por el usuario")
    parser.add_argument("--documento", default=None,
                        help="ruta a un .txt/.pdf a analizar (requerido si --modo documento)")
    parser.add_argument("--normas", nargs="*", default=None,
                        help="nombres de archivo de knowledge_base/ a usar como contexto")
    parser.add_argument("--formato", choices=[FORMATO_JSON, FORMATO_MARKDOWN],
                        default=FORMATO_JSON, help="formato de salida (por defecto: json)")
    parser.add_argument("--demo", action="store_true",
                        help="ejecuta consultas de ejemplo")
    parser.add_argument("--ver-prompt", dest="ver_prompt", action="store_true",
                        help="imprime el prompt ensamblado y termina (no llama al modelo)")
    parser.add_argument("--consulta", default="¿Qué es el derecho de retracto?",
                        help="consulta a usar junto con --ver-prompt")
    args = parser.parse_args()

    if args.modo == "documento":
        if not args.documento:
            print("[ERROR] --modo documento requiere --documento <ruta al .txt o .pdf>")
            sys.exit(1)
        try:
            cliente = ClienteLLM()
        except ErrorLLM as e:
            print(f"[ERROR de configuración] {e}")
            sys.exit(1)
        ejecutar_documento_interactivo(cliente, args.documento)
        return

    if args.ver_prompt:
        try:
            solo_ver_prompt(args.formato, args.normas, args.consulta)
        except FileNotFoundError as e:
            print(f"[ERROR] {e}")
            sys.exit(1)
        return

    try:
        cliente = ClienteLLM()
    except ErrorLLM as e:
        print(f"[ERROR de configuración] {e}")
        sys.exit(1)

    if args.demo:
        ejecutar_demo(cliente, args.formato)
    else:
        ejecutar_interactivo(cliente, args.formato, args.normas)


if __name__ == "__main__":
    main()
