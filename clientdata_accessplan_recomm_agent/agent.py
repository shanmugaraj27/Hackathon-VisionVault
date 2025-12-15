from google.adk.agents.llm_agent import Agent
from google.adk.tools.bigquery import BigQueryToolset
from google.adk.tools.bigquery import BigQueryCredentialsConfig
from google.adk.tools.bigquery.config import BigQueryToolConfig
from google.adk.tools.bigquery.config import WriteMode
from .instructions import root_agent_instruction
from .custom_bigquery_tool import BigQueryCustomTool
from callback_logging import log_query_to_model, log_model_response
import google.auth
import google.cloud.logging
from typing import Dict, Any

# Define a tool configuration to block any write operations

cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()

creds, project_id = google.auth.default()
tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)

# Uses externally-managed Application Default Credentials (ADC) by default.
# This decouples authentication from the agent / tool lifecycle.
# https://cloud.google.com/docs/authentication/provide-credentials-adc
credentials_config = BigQueryCredentialsConfig(credentials=creds)

# Instantiate a BigQuery toolset
bigquery_toolset = BigQueryToolset(
    credentials_config=credentials_config, bigquery_tool_config=tool_config
)

# Initialize custom tool
custom_tool = BigQueryCustomTool(
    project_id=project_id,
    dataset_id="VisionVault_ClientDataAccess",  # Replace with your dataset
    table_id="UserPlanMapping"        # Replace with your table
)

def get_user_info(user_id: str) -> Dict[str, Any]:
    """
    Get user information (username and plan) from BigQuery.
    
    This function fetches user details from the BigQuery table based on the provided user ID.
    
    Args:
        user_id: The user ID to look up
        
    Returns:
        Dictionary containing:
            - username: The username associated with the user ID
            - plan: The subscription plan for the user (e.g., 'Gold', 'Silver', etc.)
            
    Example:
        result = get_user_info('user123')
        # Returns: {'username': 'john_doe', 'plan': 'Gold'}
    """
    return custom_tool.fetch_user_record(user_id)

root_agent = Agent(
    model='gemini-2.5-pro',
    name='uservalidatoragent',
    description='An agent that validates a given userid.',
    instruction=root_agent_instruction,
    tools=[get_user_info],
)


