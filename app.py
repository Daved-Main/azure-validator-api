from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.image_validator import validar_vehiculo
from src.utils import limpiar_json_markdown
import json
import logging
import traceback
from fastapi.responses import JSONResponse  # ✅ AGREGAR ESTE IMPORT

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Validador de Vehículos - Azure GPT-4o",
    description="API para validación de imágenes de vehículos usando IA",
    version="1.0.0"
)

class ValidationRequest(BaseModel):
    vehicle_image: str
    plate_image: str
    mode: str = "estricto"

class ErrorResponse(BaseModel):
    error: bool
    message: str
    error_code: str
    details: str = None

@app.post("/api/validar-vehiculo", response_model=dict, responses={
    400: {"model": ErrorResponse, "description": "Error en la solicitud"},
    500: {"model": ErrorResponse, "description": "Error interno del servidor"},
    503: {"model": ErrorResponse, "description": "Servicio de IA no disponible"}
})
async def validar_vehiculo_endpoint(request: ValidationRequest):
    try:
        # Validaciones básicas
        if not request.vehicle_image or not request.plate_image:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": True,
                    "message": "Ambas imágenes son requeridas",
                    "error_code": "IMAGES_REQUIRED"
                }
            )
        
        if len(request.vehicle_image) < 100 or len(request.plate_image) < 100:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": True,
                    "message": "Las imágenes base64 parecen inválidas o demasiado cortas",
                    "error_code": "INVALID_BASE64"
                }
            )
        
        if request.mode not in ["estricto", "flexible"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": True,
                    "message": "El modo debe ser 'estricto' o 'flexible'",
                    "error_code": "INVALID_MODE"
                }
            )

        logger.info(f"Validando vehículo en modo: {request.mode}")
        
        # Procesar validación
        resultado_raw = validar_vehiculo(
            request.vehicle_image,
            request.plate_image,
            modo=request.mode
        )

        if not resultado_raw:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": True,
                    "message": "El servicio de IA no respondió",
                    "error_code": "AI_SERVICE_UNAVAILABLE"
                }
            )

        resultado_limpio = limpiar_json_markdown(resultado_raw)

        try:
            resultado = json.loads(resultado_limpio)
            # Agregar metadata
            resultado["metadata"] = {
                "mode": request.mode,
                "timestamp": "2024-01-01T00:00:00Z",
                "version": "1.0.0"
            }
            return resultado
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON: {e}\nRaw response: {resultado_raw}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": True,
                    "message": "Error procesando respuesta del modelo de IA",
                    "error_code": "INVALID_AI_RESPONSE",
                    "details": f"Respuesta cruda: {resultado_raw[:200]}..."
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error interno: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": True,
                "message": "Error interno del servidor",
                "error_code": "INTERNAL_SERVER_ERROR",
                "details": str(e)
            }
        )

@app.get("/")
def root():
    return {
        "status": "online", 
        "message": "Validador de vehículos usando Azure OpenAI GPT-4o",
        "version": "1.0.0",
        "endpoints": {
            "validar_vehiculo": "/api/validar-vehiculo"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "vehicle-validator",
        "timestamp": "2024-01-01T00:00:00Z"
    }

# Manejo global de excepciones
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Excepción global: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Error interno del servidor",
            "error_code": "UNEXPECTED_ERROR"
        }
    )