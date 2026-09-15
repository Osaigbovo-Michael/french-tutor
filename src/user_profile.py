# src/profile_service.py
from langgraph.store.memory import InMemoryStore

def merge_and_store_errors(user_id: str, new_errors: list, store: InMemoryStore):
    """
    Acts as a repository service. Deduplicates incoming grammatical errors 
    and updates the user's persistent profile in the store.
    """
    if not new_errors:
        return
        
    # Fetch existing profile
    profile = store.get(namespace=("user_profiles",), key=user_id)
    existing_data = profile.value if profile else {"persistent_mistakes": []}
    historical_rules = existing_data.get("persistent_mistakes", [])
    
    # Extract and deduplicate rules using a Set
    # only feed the LLM the general grammer rules the user breaks, not every typo.
    unique_rules = set(historical_rules)
    
    for error_obj in new_errors:
        rule = error_obj.get("rule")
        if rule:
            unique_rules.add(rule)
            
    # Commit back to the store
    store.put(
        namespace=("user_profiles",),
        key=user_id,
        value={"persistent_mistakes": list(unique_rules)}
    )