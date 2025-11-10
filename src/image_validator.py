from src.client import get_client
from src.prompts import SYSTEM_PROMPT
import logging
import time
import base64

logger = logging.getLogger(__name__)

def validar_vehiculo(vehicle_img_b64: str, plate_img_b64: str, modo="estricto"):
    openai = get_client()
    
    try:
        start_time = time.time()
        
        # Para la versión 0.28.1, usamos la API directa
        response = openai.ChatCompletion.create(
            engine="gpt-4o",  # En Azure se usa "engine" en lugar de "model"
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user", 
                    "content": f"Modo de validación: {modo}. Analiza las dos imágenes y valida el vehículo."
                }
            ],
            temperature=0.0,
            max_tokens=900
        )

        processing_time = time.time() - start_time
        logger.info(f"Validación completada en {processing_time:.2f}s - Modo: {modo}")

        if not response.choices:
            raise Exception("No se recibieron choices en la respuesta")

        return response.choices[0].message['content']

    except Exception as e:
        logger.error(f"Error en validación con Azure OpenAI: {str(e)}")
        raise Exception(f"Error en servicio de IA: {str(e)}")