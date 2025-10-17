import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_MODEL = 'mixtral-8x7b-32768'

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please add it to .env file")
