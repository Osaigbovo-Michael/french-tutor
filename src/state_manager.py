# src/state.py
import operator
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages
from langgraph.store.memory import InMemoryStore

# 1. Define the Graph State
class TutorState(TypedDict):
    # Built-in reducer: Appends new messages to the existing chat history
    messages: Annotated[list, add_messages]
    
    # Custom reducer: Appends new errors to the UI's running list for the session
    current_session_errors: Annotated[List[dict], operator.add]
    
    # No reducer: Overwrites so the state always reflects the most recent evaluation
    current_level: str

# 2. Initialize Long-Term Memory (Cross-Session Store)
# This is instantiated globally here so the exact same memory bank 
# is referenced across the entire application.
cross_session_store = InMemoryStore()

# 3. Configure Short-Term Memory (Checkpointer)
# We define the connection string here to centralize configuration.
# The actual SqliteSaver object should be instantiated via a context manager 
# in the controllers to prevent database file locking.
DB_PATH = "session_memory.db"