import os
from dotenv import load_dotenv
import openai

load_dotenv()

# Configuración para la versión 0.28.1 de OpenAI
openai.api_type = "azure"
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")

# ✅ VERIFICA QUE ESTÉS USANDO GPT-4o QUE SOPORTA VISIÓN
def get_client():
    return openai