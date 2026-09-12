"""
Ensamblado del prompt del usuario (PDF "Introducción Ingeniería Prompt").

ESTRATEGIA DE DELIMITADORES
---------------------------
Para separar de forma inequívoca el CONTEXTO (los textos normativos), las
INSTRUCCIONES y la CONSULTA del usuario, se usan etiquetas tipo XML:

    <contexto_normativo> ... </contexto_normativo>
    <consulta_usuario>   ... </consulta_usuario>
    <instrucciones>      ... </instrucciones>

Es la opción más robusta de las que menciona el enunciado (triple comilla,
triple tilde invertida ``` o etiquetas XML), porque:
  - permite anidar bloques (cada ejemplo few-shot contiene sus propias secciones);
  - reduce el riesgo de que una consulta maliciosa "se haga pasar" por instrucción
    (inyección de prompt), ya que el modelo sabe que solo <instrucciones> manda.

La alternativa vista en clase —delimitar con ``` o triple comilla— queda ilustrada
en `envolver_en_triple_backtick()` para efectos comparativos.
"""

import json
from pathlib import Path

from prompts.few_shot_examples import EJEMPLOS

RAIZ = Path(__file__).resolve().parent.parent
DIR_KB = RAIZ / "knowledge_base"


def envolver_en_triple_backtick(texto: str) -> str:
    """Delimitador alternativo (estilo clase). No se usa en el flujo principal."""
    return f"```\n{texto}\n```"


def cargar_contexto(nombres=None) -> str:
    """Lee los fragmentos normativos de ``knowledge_base/`` y los concatena.

    Parámetros
    ----------
    nombres : list[str] | None
        Lista opcional de nombres de archivo (con o sin ``.txt``) para acotar el
        contexto a normas específicas. En esta fase del proyecto es un humano quien
        decide qué normas son relevantes para cada consulta; en el Avance 2 esa
        selección la hará el componente de recuperación (RAG).
    """
    archivos = sorted(DIR_KB.glob("*.txt"))
    if nombres:
        pedidos = {n.lower().replace(".txt", "") for n in nombres}
        archivos = [a for a in archivos if a.stem.lower() in pedidos]
        faltantes = pedidos - {a.stem.lower() for a in archivos}
        if faltantes:
            raise FileNotFoundError(
                "No se encontraron estos archivos en knowledge_base/: "
                + ", ".join(sorted(faltantes))
            )
    if not archivos:
        raise FileNotFoundError(f"No hay fragmentos normativos en {DIR_KB}")

    bloques = []
    for a in archivos:
        contenido = a.read_text(encoding="utf-8").strip()
        bloques.append(f"===== FUENTE: {a.stem} =====\n{contenido}")
    return "\n\n".join(bloques)


def _render_ejemplo(ej: dict) -> str:
    salida = json.dumps(ej["respuesta"], ensure_ascii=False, indent=2)
    return (
        "<ejemplo>\n"
        f"  <contexto_normativo>\n{ej['contexto']}\n  </contexto_normativo>\n"
        f"  <consulta_usuario>\n{ej['consulta']}\n  </consulta_usuario>\n"
        f"  <respuesta_esperada>\n{salida}\n  </respuesta_esperada>\n"
        "</ejemplo>"
    )


def construir_few_shot() -> str:
    """Renderiza el bloque de ejemplos few-shot con la misma estructura de etiquetas."""
    ejemplos = "\n\n".join(_render_ejemplo(e) for e in EJEMPLOS)
    return (
        "<ejemplos>\n"
        "A continuación hay ejemplos ya resueltos. Imita EXACTAMENTE el mismo formato "
        "y el mismo criterio (fundamentar solo con el contexto) en tu respuesta.\n\n"
        f"{ejemplos}\n"
        "</ejemplos>"
    )


def construir_prompt_documento(consulta: str, documento_texto: str) -> str:
    """Arma el mensaje de usuario del modo «análisis documental» (sin few-shot ni
    normativa colombiana): solo el documento cargado, la consulta y las instrucciones.
    """
    partes = [
        f"<documento_usuario>\n{documento_texto.strip()}\n</documento_usuario>",
        f"<consulta_usuario>\n{consulta.strip()}\n</consulta_usuario>",
        (
            "<instrucciones>\n"
            "1. Responde la <consulta_usuario> usando ÚNICAMENTE el texto de "
            "<documento_usuario>.\n"
            "2. Si el documento no contiene la respuesta, decláralo de forma explícita "
            "en el campo \"respuesta\" con la frase de negación definida en la "
            "configuración del sistema.\n"
            "3. Cíñete al formato de salida JSON definido en la configuración del "
            "sistema.\n"
            "</instrucciones>"
        ),
    ]
    return "\n\n".join(partes)


def construir_prompt_usuario(
    consulta: str, contexto: str, incluir_few_shot: bool = True
) -> str:
    """Arma el mensaje de usuario completo: few-shot + contexto + consulta + instrucciones."""
    partes = []
    if incluir_few_shot:
        partes.append(construir_few_shot())
    partes.append(f"<contexto_normativo>\n{contexto.strip()}\n</contexto_normativo>")
    partes.append(f"<consulta_usuario>\n{consulta.strip()}\n</consulta_usuario>")
    partes.append(
        "<instrucciones>\n"
        "1. Responde la <consulta_usuario> usando ÚNICAMENTE el texto de "
        "<contexto_normativo>.\n"
        "2. Si el contexto no contiene la respuesta, decláralo de forma explícita "
        "(no la deduzcas ni la completes con conocimiento propio).\n"
        "3. Cíñete al formato de salida definido en la configuración del sistema.\n"
        "</instrucciones>"
    )
    return "\n\n".join(partes)
