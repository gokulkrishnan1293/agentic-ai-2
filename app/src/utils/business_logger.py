import datetime

# This is a simple, stateless logger. It just prints formatted strings.

def log_workflow_start(request_id: str):
    """Logs the start of the entire workflow."""
    print(f"[{datetime.datetime.now().isoformat()}] INFO: Agent workflow started for Request ID: {request_id}")

def log_agent_start(agent_name: str, request_id: str):
    """Logs the start of an individual agent's turn."""
    print(f"[{datetime.datetime.now().isoformat()}] INFO: --- {agent_name.upper()} INVOKED --- (ID: {request_id})")

def log_agent_thought(thought: str, request_id: str):
    """Logs the specific thought process of the Supervisor."""
    print(f"[{datetime.datetime.now().isoformat()}] INFO: Supervisor Thought: \"{thought}\"")

def log_agent_finish(agent_name: str, request_id: str, duration_ms: float):
    """Logs the completion of an agent's turn."""
    print(f"[{datetime.datetime.now().isoformat()}] INFO: --- {agent_name.upper()} FINISHED in {duration_ms:.2f}ms --- (ID: {request_id})\n")

def log_workflow_finish(request_id: str):
    """Logs the end of the entire workflow."""
    print(f"[{datetime.datetime.now().isoformat()}] INFO: Agent workflow finished for Request ID: {request_id}")


def log_simple_message(thought: str, request_id: str):
    """Logs the specific thought process of the Supervisor."""
    print(f"[{datetime.datetime.now().isoformat()}] \"{thought}\"")
