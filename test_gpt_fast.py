from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
from openai import OpenAI
import uvicorn


class GPTSummaryAPI:
    """
    Clase que define un router de FastAPI para generar resúmenes de puntos de tenis
    usando el modelo gpt-4o-mini de OpenAI.
    """

    def __init__(self, api_key: str):
        # Crea cliente OpenAI directamente con la clave pasada como texto
        self.client = OpenAI(api_key=api_key)
        self.router = APIRouter()
        self._add_routes()

    def _add_routes(self):
        """Define las rutas del router"""

        class PointData(BaseModel):
            player_a: str
            player_b: str
            point_data: list[str]

        @self.router.post("/generate_point_summary")
        async def generate_point_summary(data: PointData):
            # Mostrar en consola lo recibido
            print("\n📩 === NUEVA PETICIÓN RECIBIDA ===")
            print(f"Jugador A: {data.player_a}")
            print(f"Jugador B: {data.player_b}")
            print("Secuencia de punto:")
            for action in data.point_data:
                print("  ", action)

            prompt = f"""
Eres un comentarista de tenis experto.
Tu tarea es generar un resumen breve (máx. 20 palabras) de un punto de tenis.

Formato de punto:
Cada acción: X(actor):[tipo]:valores#resultado.
Abreviaturas:
P=potencia, Q=precisión, I=prob. entrar, R=prob. alcanzar, D=dificultad, C=capacidad,
S=saque, H=golpe, A=alcance.

Ejemplo: S({data.player_a}):P0.15-Q0.39-I0.59#IN significa que {data.player_a} realiza un saque con esos valores y entra.

Usa los valores para reflejar si los golpes son potentes, precisos o flojos.
Narra el punto en una sola frase natural.

Punto:
{data.point_data}
            """

            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Eres un comentarista de tenis experto."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=60,
                )

                summary = response.choices[0].message.content.strip()

                # Mostrar resultado en consola
                print("\n✅ RESUMEN GENERADO:")
                print(summary)
                print("\n🔹 USO DE TOKENS:")
                print(response.usage)

                return {
                    "summary": summary,
                    "usage": response.usage.model_dump()
                }

            except Exception as e:
                print("\n❌ ERROR en la generación:")
                print(str(e))
                return {"error": str(e)}


# ============================================
# 🚀 EJEMPLO DE USO LOCAL DIRECTO
# ============================================

if __name__ == "__main__":
    # 👇 Introduce aquí tu API key directamente (solo para pruebas locales)
    api_key = "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"

    app = FastAPI(title="GPT Summary Test API")

    gpt_api = GPTSummaryAPI(api_key)
    app.include_router(gpt_api.router)

    # Ejecutar el servidor local
    uvicorn.run(app, host="0.0.0.0", port=8000)
