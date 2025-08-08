import time
from functools import wraps
from typing import Callable
from src.state import AgentState, TurnLog
from src.utils.logger import log_info,log_error
from src.utils.business_logger import log_agent_finish,log_agent_start

def agent_node_wrapper(agent_func: Callable[[AgentState], dict]) -> Callable[[AgentState], dict]:
    """
    A decorator that wraps ANY agent node function (including the Supervisor).
    It provides:
    1.  Structured logging for the agent's execution turn.
    2.  Timing and performance metrics.
    3.  Automatic appending of the detailed TurnLog to the state's turn_history.
    """
    # --- THIS IS THE KEY CHANGE ---
    # We now handle the supervisor's name gracefully here.
    if agent_func.__name__ == 'run_supervisor':
        agent_name = 'supervisor'
    else:
        agent_name = agent_func.__name__.replace('run_', '')

    @wraps(agent_func)
    def wrapper(state: AgentState) -> dict: # <-- ALWAYS returns a dictionary
        """The actual wrapper that executes and logs the agent."""
        request_id = state.get('request_id', 'unknown')
        log_info(f"Wrapper starting turn for agent: '{agent_name}'.", extra={"extra_info": {"request_id": request_id}})
        log_agent_start(agent_name, request_id)

        # Determine the input for the log based on the agent
        if agent_name == 'supervisor':
            # The Supervisor's input is the history of previous turns
            input_for_log = {"turn_history_length": len(state.get("turn_history", []))}
        else:
            # Worker agents' input is the handoff payload
            input_for_log = state.get("handoff", {}).get("payload", {})
        
        start_time = time.time()
        
        try:
            # Execute the actual agent function (e.g., run_supervisor or run_analyzer)
            output_updates = agent_func(state)
        except Exception as e:
            log_error(
                f"Agent '{agent_name}' raised an unhandled exception.",
                extra={"extra_info": {"request_id": request_id, "error": str(e)}}
            )
            # Return a structured error state
            output_updates = {"status": "HALTED_AGENT_ERROR", "handoff": {"agent": "END"}}

        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        thought = f"Executed function '{agent_func.__name__}'." 
        
        # Check if the agent's output contains our special key for its thought process.
        if "__agent_thought__" in output_updates:
            # Use the agent's direct output as the thought
            thought = output_updates["__agent_thought__"]
            # Remove the special key so it doesn't pollute the final state
            del output_updates["__agent_thought__"]

        if 'turn_history' in output_updates:
            del output_updates['turn_history']
        
        # 2. Now, create the clean TurnLog for the current turn.
        #    Its 'output' field now only contains the direct results of the agent.
        turn_log_entry = TurnLog(
            agent_name=agent_name,
            input=input_for_log,
            output=output_updates.copy(), # Use a copy to be safe
            tools_used=[],
            thought_process=thought,
            tokens_used=None,
            cost_usd=None,
            duration_ms=round(duration_ms, 2)
        )
        
        # 3. Get the history of all previous turns.
        current_history = state.get("turn_history", [])
        
        # 4. Create the final, clean dictionary to be returned to the graph.
        #    It contains the agent's desired updates PLUS the new, correct history.
        final_updates = output_updates
        final_updates["turn_history"] = current_history + [turn_log_entry]
        
        log_info(
            f"Wrapper finished turn for agent: '{agent_name}'.",
            extra={"extra_info": {"request_id": request_id, "duration_ms": f"{duration_ms:.2f}"}}
        )
        log_agent_finish(agent_name, request_id, duration_ms)


        
        return final_updates

    return wrapper