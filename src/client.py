import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

# Versión corregida sin el parámetro 'proxies'
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

def get_client():
    return client