from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from PIL import Image
from io import BytesIO
import requests
import base64
import os
from dotenv import load_dotenv
import logging

load_dotenv()

app = FastAPI()

# Configurar CORS
origins = [
    "http://localhost:5175",  # URL del frontend (ajusta según sea necesario)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar logging
logging.basicConfig(level=logging.INFO)

# OpenAI API Key
api_key = os.getenv("OPENAI_API_KEY")

# Function to encode the image to base64
def encode_image(image):
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return base64_image

# Endpoint para subir la imagen
@app.post("/upload-image/")
async def upload_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(BytesIO(contents))
        colors = extract_colors(image)
        return JSONResponse(content={"colors": colors})
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

def extract_colors(image):
    base64_image = encode_image(image)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": "Analiza la imagen y dime cuál es la paleta de colores. Dame solamente los códigos de los colores en formato hexadecimal, quiero que no incluyas otro tipo de texto o comentario, solamente los codigos en hadecimal y cada uno en una linea distinta."
                },
                {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
                }
            ]
            }
        ],
        "max_tokens": 300
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        colors_text = data.get("choices", [])[0].get("message", {}).get("content", "").strip()
        colors = colors_text.split("\n")
        return colors
    except (requests.exceptions.RequestException, IndexError, KeyError) as e:
        logging.error(f"Error processing OpenAI response: {e}")
        raise ValueError(f"Error al procesar la respuesta de OpenAI: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)