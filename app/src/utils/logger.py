import logging
import json
from langchain_core.messages import convert_to_messages, BaseMessage

# ---------------------------------------------------------------------------
# SECTION 1: PRODUCTION-READY STRUCTURED LOGGER (for CloudWatch)
# ---------------------------------------------------------------------------

LOGGING_ENABLED = False

class JsonFormatter(logging.Formatter):
    """Formats log records into a JSON string."""
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        # Add extra fields passed to the logger, like claim_id or agent_name
        if hasattr(record, 'extra_info'):
            log_record.update(record.extra_info)
            
        return json.dumps(log_record)

def setup_logger():
    """Configures and returns a logger for the application."""
    # Get the logger for our specific application package
    logger = logging.getLogger("claim_processing_agent")
    
    # Prevent adding duplicate handlers if this function is called multiple times
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    logger.propagate = False
    
    # Create a handler to stream logs to the console (which is captured by Lambda/CloudWatch)
    handler = logging.StreamHandler()
    
    # Set our custom JSON formatter on the handler
    formatter = JsonFormatter()
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger

# Create a single, pre-configured logger instance that can be imported by any module.
log = setup_logger()

def log_info(*args, **kwargs):
    if LOGGING_ENABLED:
        log.info(*args, **kwargs)

def log_error(*args, **kwargs):
    if LOGGING_ENABLED:
        log.error(*args, **kwargs)


# --- HOW TO USE THE STRUCTURED LOGGER ---
#
# from ..utils.logger import log
#
# # Simple log message
# log.info("SOP Retriever Agent has started.")
#
# # Log message with rich, searchable context
# log.info(
#     "Intent classified successfully.",
#     extra={
#         "extra_info": {
#             "claim_id": "xyz-123",
#             "agent_name": "Analyzer",
#             "intent": "duplicate_claim"
#         }
#     }
# )
#
# This will produce a JSON log line in CloudWatch like:
# {
#   "timestamp": "...", "level": "INFO", "message": "Intent classified successfully.",
#   "claim_id": "xyz-123", "agent_name": "Analyzer", "intent": "duplicate_claim"
# }
#

# ---------------------------------------------------------------------------
# SECTION 2: VISUAL DEBUG LOGGER (for Local Development)
# ---------------------------------------------------------------------------

def _pretty_print_message(message: BaseMessage, indent: bool = False):
    """Internal helper to print a single message with optional indentation."""
    pretty_message = message.pretty_repr(html=True)
    if not indent:
        print(pretty_message)
        return

    indented = "\n".join("  " + line for line in pretty_message.split("\n"))
    print(indented)

def pretty_print_messages(update: dict, last_message: bool = False):
    """
    Listens to the stream from a LangGraph app and prints the messages
    from each node in a readable, color-coded format. Best for local debugging.
    """
    for node_name, node_update in update.items():
        if "__end__" not in node_name and "messages" in node_update:
            print(f"--- Update from Node: ✨ {node_name} ✨ ---")

            messages = convert_to_messages(node_update["messages"])
            if last_message:
                messages = messages[-1:]

            for m in messages:
                _pretty_print_message(m, indent=False)
            print(f"--- End of Update from {node_name} ---\n")