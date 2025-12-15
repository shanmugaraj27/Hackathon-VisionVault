from google.adk.agents.llm_agent import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools.bigquery import BigQueryToolset
from google.adk.tools.bigquery import BigQueryCredentialsConfig
from google.adk.tools.bigquery.config import BigQueryToolConfig
from google.adk.tools.bigquery.config import WriteMode
from .instructions import root_agent_instruction, analyze_enquiry_agent_instruction
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

def get_reports_services() -> Dict[str, Any]:
    """
    Get available reports and services information.
    
    Returns a static JSON response with reports services and plan availability.
    
    Returns:
        Dictionary containing:
            - Reports_Services: Product-specific subscriptions and reports
            - Sub-Reports_Services: PRA Statements & Reports (CSV/Excel)
            - Gold: Availability indicator for Gold plan
            - Silver: Availability indicator for Silver plan
            
    Example:
        result = get_reports_services()
        # Returns: {
        #     "Reports_Services": "Product-specific subscriptions and reports",
        #     "Sub-Reports_Services": "PRA Statements & Reports (CSV/Excel)",
        #     "Gold": "X",
        #     "Silver": ""
        # }
    """
    return {
        "Reports_Services": "Product-specific subscriptions and reports",
        "Sub-Reports_Services": "PRA Statements & Reports (CSV/Excel)",
        "Gold": "X",
        "Silver": ""
    }

def verify_plan_access(plan_name: str, reports_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify if the user's plan has access to the reports and services.
    
    This function takes the user's plan name and the reports/services data,
    then checks if the plan is available (has reference/availability indicator).
    
    Args:
        plan_name: The user's subscription plan name (e.g., 'Gold', 'Silver', 'Bronze')
        reports_data: Dictionary containing reports/services info and plan availability
        
    Returns:
        Dictionary containing:
            - plan: The plan name being verified
            - has_access: Boolean indicating if plan has access to reports/services
            - Reports_Services: The reports services description
            - Sub_Reports_Services: The sub-reports services description
            - message: Human-readable access status message
            
    Example:
        reports = get_reports_services()
        result = verify_plan_access('Gold', reports)
        # Returns: {
        #     'plan': 'Gold',
        #     'has_access': True,
        #     'Reports_Services': 'Product-specific subscriptions and reports',
        #     'Sub_Reports_Services': 'PRA Statements & Reports (CSV/Excel)',
        #     'message': 'Gold plan has access to reports and services'
        # }
    """
    # Check if plan_name exists in reports_data and has a non-empty availability indicator
    plan_availability = reports_data.get(plan_name, "")
    has_access = plan_availability != ""
    
    return {
        "plan": plan_name,
        "has_access": has_access,
        "Reports_Services": reports_data.get("Reports_Services", ""),
        "Sub_Reports_Services": reports_data.get("Sub-Reports_Services", ""),
        "message": f"{plan_name} plan {'has' if has_access else 'does not have'} access to reports and services"
    }



analyze_enquiry_agent = Agent(
    model='gemini-2.5-pro',
    name='analyze_enquiry_agent',
    description='An agent that categorizes a customer enquiry by matching it to services in BigQuery.',
    instruction=analyze_enquiry_agent_instruction,
    tools=[bigquery_toolset],
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
)

plan_verification_agent = Agent(
    model='gemini-2.5-pro',
    name='plan_verification_agent',
    description='An agent that verifies if a user plan has access to reports and services.',
    instruction='You are a plan verification agent. You receive the user\'s plan name and reports/services availability data. Your job is to verify if the user\'s plan has access to the available reports and services. Check if the plan name appears in the services data with a non-empty availability indicator (marked with "X"). Provide a clear answer about whether the plan has access or not.',
    tools=[verify_plan_access],
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
)

recommendation_agent = SequentialAgent(
    name='recommendation_agent',
    sub_agents=[analyze_enquiry_agent, plan_verification_agent],
)

root_agent = Agent(
    model='gemini-2.5-pro',
    name='uservalidatoragent',
    description='An agent that validates a given userid.',
    instruction=root_agent_instruction,
    tools=[get_user_info],
    sub_agents=[recommendation_agent],
)


