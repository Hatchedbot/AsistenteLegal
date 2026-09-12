# Consultor Normativo — Asistente Experto (RAG + Agentes)

Proyecto de la electiva **Desarrollo de Aplicaciones con IA** (código 56BA1A).

Sistema de IA pensado para funcionar **de forma local** (preservando la privacidad de
los datos) capaz de "leer" una base de conocimientos jurídica, responder preguntas y
apoyar tareas de orientación normativa.

> ⚠️ **Aviso:** este asistente ofrece **orientación informativa** con base en textos
> normativos. **No es asesoría jurídica** ni sustituye a un abogado.

---

## 1. Enfoque elegido

De los tres enfoques propuestos (Asistente Legal/Normativo, Tutor Académico, Analista de
Soporte Técnico) se eligió:

### 🏛️ Asistente Legal/Normativo — «Consultor Normativo»

Responde preguntas de una persona sin formación jurídica citando la norma y el artículo
que fundamentan la respuesta, y reconoce explícitamente cuándo la información **no está**
en sus fuentes (en lugar de inventarla).

### Dominio normativo del proyecto (Colombia)

| Norma | Materia |
|---|---|
| Ley 1581 de 2012 | Protección de datos personales |
| Ley 820 de 2003 | Arrendamiento de vivienda urbana |
| Ley 1480 de 2011 | Estatuto del Consumidor |
| Código Civil | Obligaciones, contratos y responsabilidad civil |
| Ley 1437 de 2011 (CPACA) | Procedimiento administrativo |
| Estatuto Tributario | Deberes formales y sanciones |
| Ley 1564 de 2012 (CGP) | Proceso civil |

**Decisión de diseño (alcance de la implementación RAG).** El corpus completo de esos
siete cuerpos normativos es muy grande y heterogéneo, lo que en la fase de recuperación
(Avance 2) genera problemas de ventana de contexto, ambigüedad entre ramas del derecho,
vocabulario compartido, fragmentación (*chunking*) y vigencia. Por eso:

- **Avance 1 (este entrega):** se declaran las siete normas y se usan **fragmentos
  representativos** de todas ellas como base de conocimiento de demostración. En esta
  fase es un humano quien selecciona qué norma es relevante para cada consulta.
- **Avance 2 (RAG):** la implementación real del recuperador se **acotará a Ley 1581,
  Ley 820 y Ley 1480** (leyes cortas, de estructura homogénea y temática afín). El resto
  queda como trabajo futuro.

---

## 2. Qué cubre el Avance 1

El Avance 1 es **exclusivamente ingeniería de prompts**. No hay recuperación automática
ni base vectorial todavía.

| Requisito del avance | Dónde está |
|---|---|
| **Diseño del System Prompt** (comportamiento del asistente) | [`src/prompts/system_prompt.py`](src/prompts/system_prompt.py) |
| **Few-Shot Prompting** (ejemplos que fijan el formato de salida) | [`src/prompts/few_shot_examples.py`](src/prompts/few_shot_examples.py) |
| **Estrategias de delimitadores** (separar contexto de instrucciones) | [`src/prompt_builder.py`](src/prompt_builder.py) |
| **Configuración del *system*** (motor LLM, roles, parámetros) | [`src/llm_client.py`](src/llm_client.py) |
| **Formato de salida** (JSON estructurado / Markdown) | `system_prompt.py` (`ESQUEMA_JSON`) |

### 2.1 System Prompt

Basado en el PDF de clase *"System configuration Chat Roles"*. Define:

- **Persona / rol acotado:** consultor normativo, **no abogado**.
- **Ámbito de conocimiento (guardrails):** solo responde con base en el texto que recibe
  dentro de `<contexto_normativo>`.
- **Lógica condicional** (PDF *"Introducción Ingeniería Prompt"*):
  - si el contexto contiene la respuesta → responde con fundamento;
  - si es jurídica pero el contexto no la cubre → *"La información solicitada no se
    encuentra en las fuentes consultadas."*;
  - si no es jurídica o está fuera del dominio → redirige e informa su alcance.
- **Formato de salida forzado** (JSON válido, sin texto adicional).
- **Tono:** español claro y formal, para público sin formación jurídica.

### 2.2 Few-Shot Prompting

Basado en el PDF *"Shot Prompting"*. Se incluyen **5 ejemplos** con casos variados
(uno de arrendamiento, uno de datos personales, uno de consumidor, uno **fuera de
alcance** y uno **sin fundamento** en el contexto), todos con el **mismo esquema JSON**,
aplicando las recomendaciones del material: *consistencia*, *variedad* y *control del
costo en tokens*.

### 2.3 Delimitadores

Basado en el PDF *"Introducción Ingeniería Prompt"*. Se usan **etiquetas tipo XML** para
separar de forma inequívoca cada bloque:

```
<contexto_normativo> ...textos de las leyes... </contexto_normativo>
<consulta_usuario>   ...la pregunta del usuario... </consulta_usuario>
<instrucciones>      ...qué debe hacer el modelo... </instrucciones>
```

Se prefieren a la triple comilla / triple tilde invertida (` ``` `) porque permiten
anidar bloques (cada ejemplo few-shot lleva sus propias secciones) y reducen el riesgo
de **inyección de prompt** desde la consulta del usuario. El delimitador alternativo con
` ``` ` queda ilustrado en `prompt_builder.envolver_en_triple_backtick()`.

### 2.4 Formato de salida (JSON)

```json
{
  "respuesta": "explicación clara para una persona sin formación jurídica",
  "fundamento_normativo": [
    { "norma": "Ley 1581 de 2012", "articulo": "Artículo 8", "cita_textual": "..." }
  ],
  "nivel_confianza": "alto | medio | bajo",
  "advertencia": "Este contenido es orientación informativa y no constituye asesoría jurídica.",
  "requiere_abogado": true
}
```

### 2.5 Modo adicional: análisis documental (`--modo documento`)

Además del Consultor Normativo (acotado a las siete normas colombianas), el CLI incluye
un segundo modo, independiente, para analizar **cualquier documento** `.txt`/`.pdf` que
cargue el usuario (contratos, manuales, políticas, etc.) con el mismo criterio de
cero-alucinación, citando siempre el fragmento textual que respalda la respuesta:

```bash
python src/main.py --modo documento --documento contrato.pdf
```

Dentro de este modo: `/otro <ruta>` cambia de documento, `/salir` termina la sesión. La
extracción de PDF usa `pypdf`; el system prompt vive en
[`src/prompts/system_prompt_documento.py`](src/prompts/system_prompt_documento.py) y es
deliberadamente **distinto** al del Consultor Normativo, porque su `<dominio>` no debe
restringirse a la normativa colombiana.

---

## 3. Arquitectura del Avance 1

```
                +---------------------------+
   knowledge_base/  ->  |  prompt_builder.py         |
   (fragmentos .txt)    |  - carga contexto          |
                        |  - arma few-shot           |
   system_prompt.py --> |  - envuelve en <etiquetas> |
   few_shot_examples.py |                           |
                        +-------------+-------------+
                                      |
                                      v
                        +---------------------------+        +------------------+
        LLM_PROVIDER --> |  llm_client.py            | -----> |  Ollama (local)  |
        (.env)           |  interfaz única generar() |   ó    |  Gemini (API)    |
                         +-------------+-------------+        +------------------+
                                      |
                                      v
                              respuesta JSON / Markdown
```

### Estructura de carpetas

```
.
├── README.md
├── requirements.txt
├── .env.example
├── src/
│   ├── main.py                 # CLI (interactivo / --demo / --ver-prompt / --modo documento)
│   ├── llm_client.py           # capa unificada Ollama + Gemini
│   ├── prompt_builder.py       # ensamblado del prompt + delimitadores
│   ├── document_loader.py      # carga .txt/.pdf para --modo documento
│   └── prompts/
│       ├── system_prompt.py            # System Instruction del Consultor Normativo
│       ├── system_prompt_documento.py  # System Instruction del modo análisis documental
│       └── few_shot_examples.py        # 5 ejemplos few-shot (Consultor Normativo)
├── knowledge_base/             # fragmentos normativos (.txt) para demostración
│   ├── ley_1581_2012.txt
│   ├── ley_820_2003.txt
│   ├── ley_1480_2011.txt
│   ├── codigo_civil.txt
│   ├── cpaca_ley_1437_2011.txt
│   ├── estatuto_tributario.txt
│   └── codigo_general_proceso_ley_1564_2012.txt
└── docs/
    ├── evidencias_ejecucion.md      # fuente Markdown del PDF de evidencias
    ├── Avance_Proyecto_Evidencias.pdf # PDF de entrega (portada + TOC + evidencias)
    ├── img/                          # capturas de pantalla usadas en el PDF
    ├── ejemplos/                     # documento de muestra para --modo documento
    └── latex/
        └── informe_avance1.tex       # plantilla LaTeX alternativa (opcional)
```

---

## 4. Cómo ejecutar

### 4.1 Requisitos

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env      # y editar
```

### 4.2 Opción A — Ollama (local, recomendado por el requisito de privacidad)

1. Instalar Ollama: <https://ollama.com>
2. Descargar un modelo: `ollama pull llama3`
3. En `.env`: `LLM_PROVIDER=ollama` y `OLLAMA_MODEL=llama3`

> **Nota de rendimiento (CPU sin GPU dedicada):** en una máquina sin GPU, la inferencia de
> Ollama es puramente por CPU y cada consulta puede tardar varios minutos, sin importar
> mucho el tamaño del modelo (`llama3` 8B y `llama3.2:3b` tardaron prácticamente lo mismo
> en pruebas sobre un Ryzen 5 3400G de 4 núcleos), porque el cuello de botella es el
> hardware, no el modelo. Además, modelos más pequeños siguen peor las instrucciones
> estrictas del System Prompt (en una prueba, `llama3.2:3b` citó una norma que **no**
> estaba en el `<contexto_normativo>` entregado, alucinando desde su conocimiento propio).
> Por eso, para el desarrollo y las pruebas del día a día se recomienda dejar
> `LLM_PROVIDER=gemini` (rápido, vía API) y usar Ollama solo puntualmente para verificar
> que el mismo prompt también funciona en el motor local — lanzarlo y contar con la
> espera, no usarlo de forma interactiva. En el Avance 2 (RAG), al enviarse solo los
> fragmentos recuperados en vez de la norma completa, el prompt será más corto y Ollama
> debería responder más rápido de forma natural.

### 4.3 Opción B — Google Gemini (API)

1. En `.env`: `LLM_PROVIDER=gemini`, `GEMINI_API_KEY=...`, `GEMINI_MODEL=gemini-2.5-flash`

### 4.4 Comandos

```bash
# Modo interactivo (usa todas las normas como contexto)
python src/main.py

# Acotar el contexto a normas concretas
python src/main.py --normas ley_1581_2012 ley_1480_2011

# Batería de consultas de ejemplo (para las capturas del PDF)
python src/main.py --demo

# Ver el prompt ensamblado SIN llamar al modelo (útil para evidenciar la estructura)
python src/main.py --ver-prompt --normas ley_820_2003 --consulta "¿Puedo terminar el arriendo antes?"

# Cambiar el formato de salida
python src/main.py --formato markdown

# Modo análisis documental: analizar un documento arbitrario (.txt/.pdf)
python src/main.py --modo documento --documento contrato.pdf
```

Dentro del modo interactivo normativo: `/salir`, `/normas a b c`, `/formato json|markdown`,
`/ver-prompt`. Dentro del modo documento: `/salir`, `/otro <ruta>`.

---

## 5. Hoja de ruta (fases siguientes)

| Fase | Contenido previsto |
|---|---|
| **Avance 2 — RAG** | Fragmentación por artículo con metadatos, indexación (TF-IDF / BM25 y/o base vectorial ChromaDB), recuperador que selecciona los fragmentos relevantes, prompt aumentado. Corpus acotado a Ley 1581, Ley 820 y Ley 1480. |
| **Avance 3 — Agentes y evaluación** | Herramientas/acciones del agente (p. ej. comparar una cláusula de contrato contra la ley), evaluación con RAGAS, *golden set* de preguntas-respuestas. |

---

## 6. Créditos

Material de clase usado como base (carpeta `MaterialDeApoyo/`, no incluida en el repo):
*Introducción Ingeniería Prompt*, *Shot Prompting*, *System configuration Chat Roles*,
*Introducción a RAG*, *Ejecución de LLMs con Ollama*.

Los archivos de `knowledge_base/` contienen **fragmentos parciales y resumidos** de
normas colombianas, reproducidos con fines académicos. No son la versión oficial ni
necesariamente la vigente; deben verificarse contra la fuente oficial.
