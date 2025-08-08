import json
import os
from langchain_core.tools import tool
from typing import Dict, Any, List
from src.config import BASE_DIR
# --- This tool simulates direct access to local data files ---
_live_data = None
_history_data = None

def _load_mock_data():
    """Helper to load mock JSONs into memory once using the correct path."""
    global _live_data, _history_data
    if _live_data is None:
        try:
            # --- THIS IS THE FIX ---
            # Correctly navigate from this file's location to the data directory.
            # os.path.dirname(__file__) -> agents/tools
            # .. -> agents
            # .. -> claim_processing_agent
            # .. -> app (project root)
            # Then down to src/knowledge_base/data
            #project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            #db_path = os.path.join(project_root, "src", "knowledge_base", "data")
            
            live_data_path = os.path.join(BASE_DIR, "knowledge_base", "data", "livedata.json")
            history_data_path = os.path.join(BASE_DIR, "knowledge_base", "data", "history.json")
            
            with open(live_data_path, 'r') as f:
                _live_data = json.load(f)
            with open(history_data_path, 'r') as f:
                _history_data = json.load(f)
            print(f"--- Data Collector Tools: Mock JSON data loaded from {db_path}. ---")
            # --- END OF FIX ---
        except Exception as e:
            print(f"--- Data Collector Tools ERROR: Could not load mock data. {e} ---")
            _live_data = {}
            _history_data = {}

@tool
def get_live_data(claim_id: str, fields: List[str]) -> Dict[str, Any]:
    """
    Fetches specific fields from the live data for a specific claim_id.
    """
    _load_mock_data()
    
    # --- THIS IS THE FIX ---
    # 1. Look up the specific claim's data dictionary.
    claim_data = _live_data.get(claim_id)
    
    if not claim_data:
        return {"error": f"Live data for claim_id '{claim_id}' not found."}
    
    # 2. Extract only the requested fields from that claim's data.
    result = {field: claim_data.get(field) for field in fields}
    return result

@tool
def get_history_data(member_id: str) -> List[Dict[str, Any]]:
    """
    Fetches the entire claim history for a given member_id.
    """
    _load_mock_data()
    return _history_data.get(member_id, [])

@tool
def finish(collected_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call this as your final step when you have successfully iterated through
    all the scenarios and collected all the necessary data.
    """
    return {"final_collected_data": collected_data}

# The Data Collector's complete, native toolbox
data_collector_tools = [get_live_data, get_history_data, finish]