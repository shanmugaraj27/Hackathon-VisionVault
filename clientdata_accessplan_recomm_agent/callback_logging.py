import logging
import json

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest


def log_query_to_model(callback_context: CallbackContext, llm_request: LlmRequest):
    if llm_request.contents and llm_request.contents[-1].role == 'user':
        for part in llm_request.contents[-1].parts:
            if part.text:
                logging.info("[query to %s]: %s", callback_context.agent_name, part.text)

def log_model_response(callback_context: CallbackContext, llm_response: LlmResponse):
    if llm_response.content and llm_response.content.parts:
        for part in llm_response.content.parts:
            if part.text:
                logging.info("[response from %s]: %s", callback_context.agent_name, part.text)
            elif part.function_call:
                logging.info("[function call from %s]: %s", callback_context.agent_name, part.function_call.name)

def suppress_json_output(callback_context: CallbackContext, llm_response: LlmResponse):
    """
    Suppress logging of JSON output from silent agents (like analyze_enquiry_agent).
    This prevents internal JSON from being logged to console/logs, but allows it to pass to next agent.
    """
    if callback_context.agent_name == "analyze_enquiry_agent":
        if llm_response.content and llm_response.content.parts:
            for part in llm_response.content.parts:
                if part.text:
                    # Check if the response is JSON
                    try:
                        json.loads(part.text.strip())
                        # If it's valid JSON, it's internal data - suppress logging only
                        logging.debug("[INTERNAL - analyze_enquiry_agent produced data (suppressed from display)]")
                        # DO NOT modify the response - just don't log it
                        return
                    except (json.JSONDecodeError, ValueError):
                        # Not JSON, log normally
                        logging.info("[response from %s]: %s", callback_context.agent_name, part.text)
    else:
        # For all other agents, log normally
        log_model_response(callback_context, llm_response)
