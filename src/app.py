# src/app.py
import sys
from pathlib import Path
import chainlit as cl

ROOT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT_DIR.parent

for path in (ROOT_DIR, PROJECT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from llm_engine import analyze_french_input

@cl.on_chat_start
async def start():
    """Sends a greeting when the user opens the app."""
    await cl.Message(
        content="Bonjour! I am your French tutor. Let's practice. What would you like to talk about today?"
    ).send()

@cl.on_message
async def main(message: cl.Message):
    """Handles incoming user messages, routes to Mistral, and formats the UI."""
    
    # 1. Display a loading message while Mistral processes the input
    loading_msg = cl.Message(content="*Réflexion en cours...*")
    await loading_msg.send()

    # 2. Send the user's text to your LLM engine (from Step 2)
    # Note: In a production app, you'd want to make analyze_french_input async, 
    # but for local testing, running it synchronously is fine.
    evaluation = analyze_french_input(message.content)

    # 3. Parse the JSON response
    tutor_reply = evaluation.get("tutor_reply", "Désolé, je n'ai pas compris.")
    corrections = evaluation.get("corrections", [])
    estimated_level = evaluation.get("estimated_level", "Unknown")

    # 4. Render the Corrections in a collapsible Step
    if corrections:
        # cl.Step creates a dropdown element in the chat window
        async with cl.Step(name="Notes du Professeur (Corrections)") as step:
            correction_markdown = ""
            for idx, corr in enumerate(corrections, 1):
                correction_markdown += f"**{idx}. Erreur:** {corr.get('error')}\n"
                correction_markdown += f"**Correction:** {corr.get('correction')}\n"
                correction_markdown += f"**Règle:** {corr.get('rule')}\n\n"
            
            # The output of the step is what shows when the user clicks to expand it
            step.output = correction_markdown

    # 5. Update the main chat bubble with the conversational reply
    # We append the CEFR level so you can track your progress
    final_output = f"{tutor_reply}\n\n*(Niveau estimé: {estimated_level})*"
    loading_msg.content = final_output
    await loading_msg.update()