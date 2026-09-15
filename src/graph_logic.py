from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.runnables import RunnableConfig

from state_manager import TutorState, DB_PATH, cross_session_store
from llm_engine import analyze_french_input
from user_profile import merge_and_store_errors


async def generate_tutor_response(state: TutorState, config: RunnableConfig, store):
    user_id = config['configurable']['user_id']
    
    # fetch user weaknesses
    profile = store.get(namespace=('user_profiles',),key=user_id)
    weaknesses = profile.value.get('persistent_mistakes', []) if profile else []
    
    formatted_messages = [{'role': m.type, 'content': m.content} for m in state['messages']]
    
    parsed_evaluation = await analyze_french_input(
        messages=formatted_messages,
        persistent_weaknesses=weaknesses
    )
    
    return {
        "messages": [("assistant", parsed_evaluation["tutor_reply"])],
        "current_session_errors": parsed_evaluation["corrections"],
        "current_level": parsed_evaluation["estimated_level"]
    }
    
    
    
async def evalute_and_store_errors(state: TutorState, config: RunnableConfig, store):
    user_id = config['configurable']['user_id']
    new_errors = state.get('current_session_errors', [])
    
    merge_and_store_errors(user_id, new_errors, store)
    
    return state


# define work flow topology
workflow = StateGraph(TutorState)

# Register the functions before connecting their edges.
workflow.add_node('inject_and_chat', generate_tutor_response)
workflow.add_node('evaluate', evalute_and_store_errors)
workflow.add_edge(START, 'inject_and_chat')
workflow.add_edge('inject_and_chat', 'evaluate')
workflow.add_edge('evaluate', END)

#execution controller

async def run_tutor_turn(user_input: str, thread_id: str, user_id: str):
    
    async with AsyncSqliteSaver.from_conn_string(DB_PATH) as checkpointer:
        
        #compile with both memory systems attched 
        tutor_app = workflow.compile(
            checkpointer=checkpointer,
            store=cross_session_store
        )
        
        run_config = {
            'configurable': {
                'thread_id': thread_id,
                'user_id': user_id
            }
        }
        
        #invoke the graph
        final_state = await tutor_app.ainvoke(
            {'messages': [{'role': 'user', 'content': user_input}]},
            run_config
        )
        
        return final_state