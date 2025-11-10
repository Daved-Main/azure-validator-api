from src.client import get_client
from src.prompts import SYSTEM_PROMPT
import logging
import time

logger = logging.getLogger(__name__)

def validar_vehiculo(vehicle_img_b64: str, plate_img_b64: str, modo="estricto"):
    client = get_client()
    
    try:
        start_time = time.time()
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Modo de validación: {modo}"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{vehicle_img_b64}"}
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{plate_img_b64}"}
                        },
                        {"type": "text", "text": "Analiza las dos imágenes y valida el vehículo."}
                    ]
                }
            ],
            temperature=0.0,
            max_tokens=900,
            timeout=30  # 30 segundos timeout
        )

        processing_time = time.time() - start_time
        logger.info(f"Validación completada en {processing_time:.2f}s - Modo: {modo}")

        if not response.choices:
            raise Exception("No se recibieron choices en la respuesta")

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Error en validación con Azure OpenAI: {str(e)}")
        raise Exception(f"Error en servicio de IA: {str(e)}")