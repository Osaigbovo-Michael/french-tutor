# src/app.py
import sys
import uuid
from pathlib import Path
import chainlit as cl
from graph_logic import run_tutor_turn

#import payload and increase the decode limit to prevent future crashes
from engineio.payload import Payload
Payload.max_decode_packets = 1000

ROOT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT_DIR.parent

for path in (ROOT_DIR, PROJECT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


@cl.on_chat_start
async def start():
    """initializes session identifiers when the user opens the app."""
    
    #generate chat specific id
    cl.user_session.set('thread_id', str(uuid.uuid4()))
    
    #hard coded user id for local development
    cl.user_session.set('user_id', 'student_alpha')
    
    await cl.Message(
        content="Bonjour! I am your French tutor. Let's practice. What would you like to talk about today?"
    ).send()

@cl.on_message
async def main(message: cl.Message):
    """Handles incoming user messages, routes to LangGraph, and formats the UI."""
    
    #retrieve session ids
    thread_id = cl.user_session.get('thread_id')
    user_id = cl.user_session.get('user_id')
    
    #loading state
    loading_msg = cl.Message(content='**Réflexion en cours...*')
    await loading_msg.send()
    
    #route input through LangGraph
    final_state = await run_tutor_turn(
        user_input=message.content,
        thread_id=thread_id,
        user_id=user_id
    )
    
    #extract data from LangGraph state
    ai_message = final_state['messages'][-1]
    
    #extract text
    tutor_reply = ai_message[-1] if isinstance(ai_message, tuple) else ai_message.content
    
    corrections = final_state.get('current_session_errors', [])
    estimated_level = final_state.get('current_level', 'Unknown')


    #Render the Corrections in a collapsible Step
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

    #Update the main chat bubble with the conversational reply
    # We append the CEFR level so you can track your progress
    final_output = f"{tutor_reply}\n\n*(Niveau estimé: {estimated_level})*"
    loading_msg.content = final_output
    await loading_msg.update()