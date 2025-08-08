from typing import TypedDict, Annotated, List, Dict, Any, Optional

class TurnLog(TypedDict):
    """
    A structured log for a single agent's execution turn.
    This is the format that will be saved in the audit trail.
    """
    agent_name: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    tools_used: List[Dict[str, Any]]
    thought_process: str
    tokens_used: Optional[int]
    cost_usd: Optional[float]
    duration_ms: Optional[float]

class AgentState(TypedDict):
    """
    The lean, in-memory state for the LangGraph workflow. It acts as a "case file"
    that is passed between agents, with the Supervisor reasoning over the turn_history.
    """
    
    # === Core Identifier & Initial Data ===
    
    request_id: str
    """The unique ID for the entire claim processing request."""

    initial_input: Dict[str, Any]
    """
    The original, unmodified event data that triggered this workflow
    (e.g., {"user_message": "...", "claim_id": "..."}).
    """
    
    # === The Case File / Memory ===
    
    turn_history: List[TurnLog]
    ""