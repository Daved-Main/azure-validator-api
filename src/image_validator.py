from src.client import get_client
from src.prompts import SYSTEM_PROMPT
import logging
import time
import base64
import json
import traceback

logger = logging.getLogger(__name__)

def validar_vehiculo(vehicle_img_b64: str, plate_img_b64: str, modo="estricto"):
    openai = get_client()
    
    try:
        start_time = time.time()
        
        # ✅ CORREGIDO: Incluir las imágenes en el request
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user", 
                "content": [
                    {
                        "type": "text",
                        "text": f"Modo de validación: {modo}. Analiza las dos imágenes y valida el vehículo."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{vehicle_img_b64}"
                        }
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{plate_img_b64}"
                        }
                    }
                ]
            }
        ]

        logger.info(f"📤 Enviando {len(messages)} mensajes a GPT-4o")
        logger.info(f"📸 Imagen vehículo (primeros 100 chars): {vehicle_img_b64[:100]}...")
        logger.info(f"📸 Imagen placa (primeros 100 chars): {plate_img_b64[:100]}...")

        # Para la versión 0.28.1, usamos la API directa
        response = openai.ChatCompletion.create(
            engine="gpt-4o",  # En Azure se usa "engine" en lugar de "model"
            messages=messages,
            temperature=0.0,
            max_tokens=900
        )

        processing_time = time.time() - start_time
        logger.info(f"✅ Validación completada en {processing_time:.2f}s - Modo: {modo}")

        if not response.choices:
            raise Exception("No se recibieron choices en la respuesta")

        result_content = response.choices[0].message['content']
        logger.info(f"📄 Respuesta GPT-4o: {result_content[:200]}...")
        
        return result_content

    except Exception as e:
        logger.error(f"❌ Error en validación con Azure OpenAI: {str(e)}")
        logger.error(f"🔍 Stack trace: {traceback.format_exc()}")
        raise Exception(f"Error en servicio de IA: {str(e)}")