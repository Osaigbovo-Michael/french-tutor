# src/llm_engine.py
import sys
from pathlib import Path
import json
import ollama
from ollama import AsyncClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.prompts import EVALUATOR_SYSTEM_PROMPT

async def analyze_french_input(user_message: str) -> dict:
    """Sends user text to Mistral and returns the parsed JSON evaluation."""
    try:
        response = ollama.chat(
            model='mistral',
            messages=[
                {'role': 'system', 'content': EVALUATOR_SYSTEM_PROMPT},
                {'role': 'user', 'content': user_message}
            ],
            format='json' # Enforces JSON schema on local Mistral
        )
        
        # Parse the JSON string into a Python dictionary
        return json.loads(response['message']['content'])
    
        
        
    except Exception as e:
        print(f"Error communicating with Mistral: {e}")
        return {
            "tutor_reply": "Désolé, j'ai rencontré un problème.",
            "corrections": [],
            "estimated_level": "A1"
        }