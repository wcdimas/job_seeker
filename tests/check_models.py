import os
from google import genai
from dotenv import load_dotenv

env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(env_path)

# Certifique-se de que sua GEMINI_API_KEY está exportada no terminal ou carregada pelo dotenv
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("--- Modelos disponíveis na sua chave ---")
try:
    # Apenas itera e imprime o nome exato de cada modelo que a chave acessa
    for model in client.models.list():
        print(f"- {model.name}")
except Exception as e:
    print(f"Erro ao consultar a API: {e}")