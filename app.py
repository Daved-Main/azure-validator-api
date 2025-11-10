from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.image_validator import validar_vehiculo
from src.utils import limpiar_json_markdown
import json
import os
import logging
import traceback
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Validador de Vehículos - Azure GPT-4o",
    description="API para validación de imágenes de vehículos usando IA",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        
        # ✅ MEJOR LOGGING PARA DEBUG
        logger.info(f"📥 Recibida solicitud - Modo: {request.mode}")
        logger.info(f"📊 Tamaño imagen vehículo: {len(request.vehicle_image)}")
        logger.info(f"📊 Tamaño imagen placa: {len(request.plate_image)}")
        logger.info(f"🔍 Primeros chars vehículo: {request.vehicle_image[:50]}...")
        logger.info(f"🔍 Primeros chars placa: {request.plate_image[:50]}...")

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

        logger.info(f"🔍 Iniciando validación con Azure GPT-4o - Modo: {request.mode}")
        
        # Procesar validación
        resultado_raw = validar_vehiculo(
            request.vehicle_image,
            request.plate_image,
            modo=request.mode
        )

        logger.info(f"✅ Respuesta recibida de Azure: {resultado_raw[:200]}...")

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
            
            logger.info(f"🎯 Validación completada - Válido: {resultado.get('valido', False)}")
            return resultado
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando JSON: {e}\nRaw response: {resultado_raw}")
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
        logger.error(f"💥 Error interno: {str(e)}\n{traceback.format_exc()}")
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
            "validar_vehiculo": "/api/validar-vehiculo",
            "health_check": "/health"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "vehicle-validator",
        "timestamp": "2024-01-01T00:00:00Z"
    }

# Health check más detallado
@app.get("/health/detailed")
def health_detailed():
    try:
        # Verificar que las variables de entorno estén configuradas
        required_env_vars = [
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT", 
            "AZURE_OPENAI_API_VERSION"
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "missing_environment_variables": missing_vars,
                    "message": "Faltan variables de entorno requeridas"
                }
            )
        
        return {
            "status": "healthy",
            "service": "vehicle-validator",
            "environment": "production",
            "timestamp": "2024-01-01T00:00:00Z",
            "checks": {
                "environment_variables": "ok",
                "api_connectivity": "pending"  # No verificamos conexión real a Azure aquí
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "message": "Health check failed"
            }
        )

# Endpoint para verificar la configuración (solo desarrollo)
@app.get("/debug/config")
def debug_config():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    config = {
        "azure_openai_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", "NOT_SET"),
        "azure_openai_api_version": os.getenv("AZURE_OPENAI_API_VERSION", "NOT_SET"),
        "azure_openai_api_key_set": bool(os.getenv("AZURE_OPENAI_API_KEY")),
        "engine": "gpt-4o"
    }
    
    # Ocultar la clave API real por seguridad
    if config["azure_openai_api_key_set"]:
        config["azure_openai_api_key"] = "SET"
    else:
        config["azure_openai_api_key"] = "NOT_SET"
    
    return config

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

# Manejo de 404
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": True,
            "message": "Endpoint no encontrado",
            "error_code": "ENDPOINT_NOT_FOUND"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)