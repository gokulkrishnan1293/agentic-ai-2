""" #from future import annotations
from langgraph.graph import StateGraph
from src.agent import analyzer_agent,sop_retriever_agent,data_collector_agent,fixer_agent,execution_sop_agent,validator_feedback_agent
from src.agent.supervisor import supervisor
from langgraph.graph import END,START,MessagesState
#from src.utils.handoff import create_handoff_tool
from src.state import AgentState
#from src.agent_map import AGENT
from src.utils.logger import pretty_print_messages
from langgraph.checkpoint.memory import InMemorySaver

graph_builder = StateGraph(AgentState)

graph_builder.add_node("supervisor",supervisor, destinations=("analyzer_agent","sop_retriever_agent"
,"fixer_agent","validator_feedback_agent",
"data_collector_agent","execution_sop_agent", END))


graph_builder.add_node("analyzer_agent",analyzer_agent)
graph_builder.add_node("sop_retriever_agent",sop_retriever_agent)
graph_builder.add_node("data_collector_agent",data_collector_agent)
graph_builder.add_node("execution_sop_agent",execution_sop_agent)
graph_builder.add_node("validator_feedback_agent",validator_feedback_agent)
graph_builder.add_node("fixer_agent",fixer_agent)
graph_builder.add_edge(START, "supervisor")

graph_builder.add_edge("analyzer_agent", "supervisor")
graph_builder.add_edge("sop_retriever_agent", "supervisor")
graph_builder.add_edge("data_collector_agent", "supervisor")
graph_builder.add_edge("execution_sop_agent", "supervisor")
graph_builder.add_edge("fixer_agent", "supervisor")
graph_builder.add_edge("validator_feedback_agent", "supervisor")
graph = graph_builder.compile()
 """


from langgraph.graph import StateGraph, END, START
from src.state import AgentState
from src.agent import  analyzer,sop_retriever,data_collector,execution_sop # etc.
from src.agent.supervisor import run_supervisor,route_from_supervisor

# Import BOTH wrappers now
from src.utils.agent_wrapper import agent_node_wrapper

# --- Node and Agent Definitions ---

# The worker agents are wrapped for logging.
AGENT_MAP = {
    "System Validator Agent": agent_node_wrapper(analyzer.run_system_validator),
    "Claim Pend Agent":agent_node_wrapper(sop_retriever.run_claim_pend),
    "Claim Detail Extractor Agent":agent_node_wrapper(data_collector.run_claims_details_extractor),
    "Duplicate Review Agent":agent_node_wrapper(execution_sop.run_duplicate_review_agent),
}

# The Supervisor is ALSO wrapped, as it's a standard node now.
SUPERVISOR_NODE = agent_node_wrapper(run_supervisor)

# --- Graph Definition ---
graph_builder = StateGraph(AgentState)

# 1. Add the Supervisor as a STANDARD node
graph_builder.add_node("supervisor", SUPERVISOR_NODE)

# 2. Add all the worker agent nodes from the map
for name, agent_node in AGENT_MAP.items():
    graph_builder.add_node(name, agent_node)

# 3. Define the entry point
graph_builder.add_edge(START, "supervisor")

# 4. Define the routing FROM the Supervisor using a CONDITIONAL EDGE
# This is the key change that resolves the error.
path_map = {name: name for name in AGENT_MAP.keys()}
path_map["END"] = END

graph_builder.add_conditional_edges(
    "supervisor",
    route_from_supervisor,
    path_map=path_map
)

# 5. Define the routing FROM all workers BACK to the Supervisor
for name in AGENT_MAP.keys():
    graph_builder.add_edge(name, "supervisor")

# 6. Compile the graph
graph = graph_builder.compile()

