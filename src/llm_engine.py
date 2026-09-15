# src/llm_engine.py
import sys
from pathlib import Path
import json
from ollama import AsyncClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.prompts import EVALUATOR_SYSTEM_PROMPT

# Allow enough time for a local model's first load and generation.
ollama_client = AsyncClient(timeout=180.0)

async def analyze_french_input(messages: list, persistent_weaknesses: list = None) -> dict:
    """
    Acts as a reusable service layer. Takes a message history and optional weaknesses, 
    injects them into the system prompt, and returns the parsed JSON evaluation.
    """
    try:
        # 1. Format the dynamic prompt
        weaknesses_str = ", ".join(persistent_weaknesses) if persistent_weaknesses else "None yet."
        system_content = EVALUATOR_SYSTEM_PROMPT.replace(
            "{weaknesses}", weaknesses_str
        )
        
        # 2. Prepend the system prompt to the ongoing conversation history
        full_message_chain = [{'role': 'system', 'content': system_content}] + messages

        # 3. Call the local model asynchronously
        response = await ollama_client.chat(
            model='qwen2.5:3b',
            messages=full_message_chain,
            format='json'
        )
        
        return json.loads(response['message']['content'])
        
    except Exception as e:
        print(f"Error communicating with qwen2.5:3b: {e}")
        return {
            "tutor_reply": "Désolé, j'ai rencontré un problème de connexion.",
            "corrections": [],
            "estimated_level": "A1"
        }