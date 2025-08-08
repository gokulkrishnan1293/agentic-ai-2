import json
import uuid
import boto3

# Import our core application components
from src.graph import graph
from src.state import AgentState
from src.utils.logger import log_info,log_error

# --- AWS Service Clients ---
# Initialize outside the handler for performance and reuse.
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
state_table = dynamodb.Table("test")

def save_final_trace_to_dynamodb(state: AgentState):

    """Saves the final, complete trace to DynamoDB for auditing."""
    request_id = state["request_id"]
    log_info("Saving final trace to DynamoDB.", extra={"extra_info": {"request_id": request_id}})
    try:
        # The entire state with the rich turn_history is our audit log.
        # We just need to ensure all parts are serializable.
        # This is a placeholder for a more robust serialization function if needed.

        item_to_save = {
            "request_id": request_id,
            "initial_input": json.loads(state.get("initial_input", {})),
            "turn_history": json.loads(state.get("turn_history", [])),
        }
        state_table.put_item(Item=item_to_save)
        log_info("Final trace saved successfully.", extra={"extra_info": {"request_id": request_id}})
    except Exception as e:
        log_error(
            "Failed to save final trace to DynamoDB.",
            extra={"extra_info": {"request_id": request_id, "error": str(e)}}
        )

# --- The Main Lambda Handler ---
def lambda_handler(event: dict, context: object) -> dict:
    """
    The main entry point for the AWS Lambda function, triggered by a direct
    invocation event (e.g., from API Gateway or the Lambda test console).
    """
    log_info("Lambda invocation started.", extra={"extra_info": {"aws_request_id": 1}})

    # 1. Parse the incoming request
    try:
        # If invoked via API Gateway, the actual event is in the 'body' field.
        if "body" in event and isinstance(event["body"], str):
            body = json.loads(event["body"])
        else:
            # If invoked directly (e.g., from the test console), the event is the body.
            body = event
        
        #user_message = body['user_message']
        request_id =  f"session-{uuid.uuid4().hex}"
        
    except (KeyError, TypeError, json.JSONDecodeError) as e:
        error_message = f"Invalid input format. Request must be a JSON object with a 'user_message' key. Error: {str(e)}"
        log_error(error_message, extra={"extra_info": {"raw_event": event}})
        return {'statusCode': 400, 'body': json.dumps({"error": error_message})}

    log_info("Starting workflow.", extra={"extra_info": {"request_id": request_id}})

    # 2. Initialize the state for the graph
    initial_state: AgentState = {
        "request_id": request_id,
        "initial_input": body,
        "turn_history": [],
        "handoff": None,
        "final_output": None,
    }
    
    # 3. Run the ENTIRE graph loop in this single invocation
    # Use app.invoke() for a synchronous call that returns the final state.
    final_state = graph.invoke(initial_state, {"recursion_limit": 25})
    log_error(final_state)
    # 4. Save the complete trace to DynamoDB for auditing
    save_final_trace_to_dynamodb(final_state)
    
    # 5. Prepare a clean response for the client
    response_payload = final_state.get("final_output", {})

    log_info("Lambda invocation completed successfully.", extra={"extra_info": {"request_id": request_id}})
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(response_payload)
    }

#lambda_handler({'claim_id':'27713M2314','warning reason':'possble diuplicare'},{})