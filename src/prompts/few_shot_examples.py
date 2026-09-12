"""
Ejemplos Few-Shot (PDF "Shot Prompting").

Se proporcionan 5 ejemplos resueltos que cubren casos VARIADOS, todos con el
MISMO formato de salida, para fijar el patrón de respuesta del modelo:

  1. Caso CON fundamento  -> arrendamiento (Ley 820 de 2003)
  2. Caso CON fundamento  -> datos personales (Ley 1581 de 2012)
  3. Caso CON fundamento  -> consumidor / derecho de retracto (Ley 1480 de 2011)
  4. Caso FUERA DE ALCANCE -> la consulta no es de naturaleza jurídica
  5. Caso SIN fundamento   -> consulta jurídica válida que el contexto no cubre

Recomendaciones del material aplicadas:
  - Consistencia: los 5 ejemplos usan exactamente el mismo esquema JSON.
  - Variedad: se incluye un caso positivo, uno fuera de alcance y uno sin fundamento.
  - Costo: se limita a 5 ejemplos para equilibrar precisión y tokens de entrada.

Cada ejemplo lleva el `contexto` que se le habría entregado al modelo, de modo que
el patrón aprendido sea "responder SÓLO con base en el contexto".
"""

EJEMPLOS = [
    # 1. CON fundamento — Ley 820 de 2003 (arrendamiento)
    {
        "contexto": (
            "Ley 820 de 2003, Artículo 24. Terminación por parte del arrendatario. "
            "El arrendatario podrá dar por terminado unilateralmente el contrato de "
            "vivienda urbana dentro del término inicial o durante sus prórrogas, "
            "avisando por escrito con no menos de tres (3) meses de anticipación y "
            "pagando una indemnización equivalente al precio de tres (3) meses de "
            "arrendamiento."
        ),
        "consulta": "Vivo en arriendo y me quiero salir antes de que se acabe el contrato. ¿Puedo?",
        "respuesta": {
            "respuesta": (
                "Sí. Como arrendatario puede terminar el contrato antes de tiempo, "
                "pero debe cumplir dos requisitos: avisar por escrito con al menos tres "
                "meses de anticipación y pagar una indemnización igual a tres meses de "
                "arriendo."
            ),
            "fundamento_normativo": [
                {
                    "norma": "Ley 820 de 2003",
                    "articulo": "Artículo 24",
                    "cita_textual": (
                        "avisando por escrito con no menos de tres (3) meses de "
                        "anticipación y pagando una indemnización equivalente al precio "
                        "de tres (3) meses de arrendamiento."
                    ),
                }
            ],
            "nivel_confianza": "alto",
            "advertencia": "Este contenido es orientación informativa y no constituye asesoría jurídica.",
            "requiere_abogado": False,
        },
    },
    # 2. CON fundamento — Ley 1581 de 2012 (datos personales)
    {
        "contexto": (
            "Ley 1581 de 2012, Artículo 8. Derechos de los titulares. El titular de los "
            "datos personales tendrá los siguientes derechos: a) Conocer, actualizar y "
            "rectificar sus datos personales frente a los responsables o encargados del "
            "tratamiento; b) Solicitar prueba de la autorización otorgada al responsable; "
            "e) Revocar la autorización y/o solicitar la supresión del dato cuando en el "
            "tratamiento no se respeten los principios, derechos y garantías legales.\n"
            "Artículo 14. Consultas. Las consultas deberán ser atendidas en un término "
            "máximo de diez (10) días hábiles contados a partir de la fecha de su recibo."
        ),
        "consulta": "¿Qué puedo exigirle a una empresa sobre mis datos y en cuánto tiempo debe responderme una consulta?",
        "respuesta": {
            "respuesta": (
                "Usted puede conocer, actualizar y rectificar sus datos, pedir prueba de "
                "la autorización que dio y revocar esa autorización o pedir que borren el "
                "dato si no se respetan sus garantías. La empresa debe atender una "
                "consulta en máximo diez (10) días hábiles desde que la recibe."
            ),
            "fundamento_normativo": [
                {
                    "norma": "Ley 1581 de 2012",
                    "articulo": "Artículo 8",
                    "cita_textual": (
                        "Conocer, actualizar y rectificar sus datos personales frente a "
                        "los responsables o encargados del tratamiento."
                    ),
                },
                {
                    "norma": "Ley 1581 de 2012",
                    "articulo": "Artículo 14",
                    "cita_textual": (
                        "Las consultas deberán ser atendidas en un término máximo de diez "
                        "(10) días hábiles contados a partir de la fecha de su recibo."
                    ),
                },
            ],
            "nivel_confianza": "alto",
            "advertencia": "Este contenido es orientación informativa y no constituye asesoría jurídica.",
            "requiere_abogado": False,
        },
    },
    # 3. CON fundamento — Ley 1480 de 2011 (retracto)
    {
        "contexto": (
            "Ley 1480 de 2011, Artículo 47. Retracto. En todos los contratos para la "
            "venta de bienes y prestación de servicios mediante sistemas de financiación "
            "otorgada por el productor o proveedor, venta de tiempos compartidos o ventas "
            "que utilizan métodos no tradicionales o a distancia, se entenderá pactado el "
            "derecho de retracto por parte del consumidor. El término máximo para ejercer "
            "el derecho de retracto será de cinco (5) días hábiles contados a partir de la "
            "entrega del bien o de la celebración del contrato en caso de prestación de "
            "servicios."
        ),
        "consulta": "Compré unos zapatos por una tienda online y ya no los quiero. ¿Puedo arrepentirme y devolverlos?",
        "respuesta": {
            "respuesta": (
                "Sí. En las compras a distancia (por internet) la ley reconoce el derecho "
                "de retracto: usted puede arrepentirse y deshacer la compra dentro de los "
                "cinco (5) días hábiles siguientes a la entrega del producto, sin necesidad "
                "de justificar el motivo. El vendedor debe devolverle el dinero."
            ),
            "fundamento_normativo": [
                {
                    "norma": "Ley 1480 de 2011",
                    "articulo": "Artículo 47",
                    "cita_textual": (
                        "El término máximo para ejercer el derecho de retracto será de "
                        "cinco (5) días hábiles contados a partir de la entrega del bien."
                    ),
                }
            ],
            "nivel_confianza": "alto",
            "advertencia": "Este contenido es orientación informativa y no constituye asesoría jurídica.",
            "requiere_abogado": False,
        },
    },
    # 4. FUERA DE ALCANCE — la consulta no es jurídica
    {
        "contexto": "(No se entregó contexto normativo para esta consulta.)",
        "consulta": "¿Me conviene comprar dólares esta semana o espero a que baje el precio?",
        "respuesta": {
            "respuesta": (
                "Esa consulta es de tipo financiero y está fuera de mi alcance. Soy un "
                "asistente de orientación sobre normativa colombiana (protección de datos, "
                "arrendamiento, consumidor, civil, administrativo, tributario y procesal). "
                "Puedo ayudarle si su pregunta es sobre alguna de esas materias."
            ),
            "fundamento_normativo": [],
            "nivel_confianza": "bajo",
            "advertencia": "Este contenido es orientación informativa y no constituye asesoría jurídica.",
            "requiere_abogado": False,
        },
    },
    # 5. SIN fundamento — consulta jurídica válida, pero el contexto no la cubre
    {
        "contexto": (
            "Ley 820 de 2003, Artículo 18. Reajuste del canon. Cada doce (12) meses de "
            "ejecución del contrato bajo un mismo precio, el arrendador podrá incrementar "
            "el canon hasta en una proporción que no sea superior al ciento por ciento "
            "(100%) del incremento que haya tenido el índice de precios al consumidor en "
            "el año calendario inmediatamente anterior."
        ),
        "consulta": "¿Cuántos días tengo para pagar el arriendo antes de que el arrendador pueda demandarme?",
        "respuesta": {
            "respuesta": "La información solicitada no se encuentra en las fuentes consultadas.",
            "fundamento_normativo": [],
            "nivel_confianza": "bajo",
            "advertencia": "Este contenido es orientación informativa y no constituye asesoría jurídica.",
            "requiere_abogado": True,
        },
    },
]
