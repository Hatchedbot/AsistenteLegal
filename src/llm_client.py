"""
Capa de acceso al modelo de lenguaje.

Unifica dos motores bajo una sola interfaz (`ClienteLLM.generar`):

  - Ollama  -> ejecución LOCAL, sin costo, offline. PDF "Ejecución de LLMs con Ollama".
  - Gemini  -> API de Google. PDF "System configuration Chat Roles".

El motor se elige con la variable de entorno ``LLM_PROVIDER`` (``ollama`` | ``gemini``).
Ambos reciben la MISMA `system_instruction` y el MISMO prompt de usuario, de modo
que el trabajo de ingeniería de prompts sea independiente del proveedor.
"""

import os


class ErrorLLM(RuntimeError):
    """Error controlado al configurar o consultar el modelo."""


class ClienteLLM:
    def __init__(self):
        self.proveedor = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
        self.max_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "2048"))
        self.temperatura = 0.2  # respuestas estables y poco creativas para un dominio legal

        if self.proveedor == "ollama":
            self.modelo = os.getenv("OLLAMA_MODEL", "llama3")
        elif self.proveedor == "gemini":
            self.modelo = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        else:
            raise ErrorLLM(
                f"LLM_PROVIDER no reconocido: '{self.proveedor}'. Use 'ollama' o 'gemini'."
            )

    def describir(self) -> str:
        return f"{self.proveedor} · modelo={self.modelo} · max_tokens={self.max_tokens}"

    def generar(self, system_prompt: str, user_prompt: str, formato_json: bool = True) -> str:
        if self.proveedor == "ollama":
            return self._generar_ollama(system_prompt, user_prompt, formato_json)
        return self._generar_gemini(system_prompt, user_prompt, formato_json)

    # ------------------------------------------------------------------ Ollama
    def _generar_ollama(self, system_prompt, user_prompt, formato_json):
        try:
            import ollama
        except ImportError as e:
            raise ErrorLLM("Falta la librería 'ollama'. Instale con: pip install ollama") from e

        try:
            respuesta = ollama.chat(
                model=self.modelo,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                format="json" if formato_json else "",
                options={"num_predict": self.max_tokens, "temperature": self.temperatura},
            )
            return respuesta["message"]["content"]
        except ErrorLLM:
            raise
        except Exception as e:
            raise ErrorLLM(
                f"No se pudo consultar Ollama (modelo '{self.modelo}'). "
                f"Verifique que el servicio esté corriendo y que el modelo esté descargado "
                f"(ollama pull {self.modelo}). Detalle: {e}"
            ) from e

    # ------------------------------------------------------------------ Gemini
    def _generar_gemini(self, system_prompt, user_prompt, formato_json):
        try:
            from google import genai
            from google.genai import types
        except ImportError as e:
            raise ErrorLLM(
                "Falta la librería 'google-genai'. Instale con: pip install google-genai"
            ) from e

        clave = os.getenv("GEMINI_API_KEY")
        if not clave:
            raise ErrorLLM("Falta GEMINI_API_KEY en el entorno (archivo .env).")

        try:
            client = genai.Client(api_key=clave)
            configuracion = types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=self.max_tokens,
                temperature=self.temperatura,
                response_mime_type="application/json" if formato_json else "text/plain",
            )
            respuesta = client.models.generate_content(
                model=self.modelo,
                config=configuracion,
                contents=user_prompt,
            )
            return respuesta.text
        except ErrorLLM:
            raise
        except Exception as e:
            raise ErrorLLM(
                f"No se pudo consultar Gemini (modelo '{self.modelo}'). Detalle: {e}"
            ) from e
