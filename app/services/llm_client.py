from groq import Groq

from app.config import GROQ_API_KEY, MODEL_NAME

# Single shared client instance, reused across the app.
client = Groq(api_key=GROQ_API_KEY)
