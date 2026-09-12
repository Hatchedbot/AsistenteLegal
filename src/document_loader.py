"""
Carga de documentos arbitrarios (.txt / .pdf) para el modo de análisis documental.

Inspirado en el prototipo `asistente.py` (carpeta BetaPRelectiva1), que usaba PyPDF2
para extraer texto de PDFs. Aquí se usa `pypdf` (el sucesor mantenido de PyPDF2) y se
homogeneiza el manejo de errores para que `main.py` pueda mostrarlos de forma consistente
con el resto del CLI.
"""

from pathlib import Path


def leer_documento(ruta: str) -> str:
    """Lee un archivo .txt o .pdf y devuelve su texto plano.

    Lanza `FileNotFoundError` si la ruta no existe, `ValueError` si el formato no está
    soportado o si el documento no tiene texto extraíble (p. ej. un PDF escaneado sin
    capa de texto).
    """
    ruta_p = Path(ruta)
    if not ruta_p.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {ruta}")

    sufijo = ruta_p.suffix.lower()
    if sufijo == ".txt":
        texto = ruta_p.read_text(encoding="utf-8")
    elif sufijo == ".pdf":
        texto = _leer_pdf(ruta_p)
    else:
        raise ValueError(f"Formato no soportado: '{sufijo}' (use .txt o .pdf)")

    if not texto.strip():
        raise ValueError(
            "El documento está vacío o es un PDF escaneado sin texto seleccionable."
        )
    return texto.strip()


def _leer_pdf(ruta: Path) -> str:
    from pypdf import PdfReader

    lector = PdfReader(str(ruta))
    paginas = []
    for pagina in lector.pages:
        texto_pagina = pagina.extract_text()
        if texto_pagina:
            paginas.append(texto_pagina)
    return "\n".join(paginas)
