from google.adk.agents.llm_agent import Agent
from google.adk.agents import SequentialAgent
from .instructions import root_agent_instruction, analyze_enquiry_agent_instruction, planverification_agent_instruction
import logging
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_user_info(user_id: str) -> Dict[str, Any]:
    """
    Get user information (username and plan) from BigQuery.
    
    Args:
        user_id: The user ID to look up
        
    Returns:
        Dictionary containing username and plan
    """
    try:
        from .custom_bigquery_tool import BigQueryCustomTool
        import google.auth
        
        creds, project_id = google.auth.default()
        custom_tool = BigQueryCustomTool(
            project_id=project_id,
            dataset_id="VisionVault_ClientDataAccess",
            table_id="UserPlanMapping"
        )
        return custom_tool.fetch_user_record(user_id)
    except Exception as e:
        logger.error(f"Error fetching user info: {e}")
        return {"username": None, "plan": None, "error": str(e)}

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
    description='An agent that categorizes a customer enquiry by matching it to services.',
    instruction=analyze_enquiry_agent_instruction,
    tools=[get_reports_services],
)

plan_verification_agent = Agent(
    model='gemini-2.5-pro',
    name='plan_verification_agent',
    description='An agent that verifies if a user plan has access to reports and services.',
    instruction=planverification_agent_instruction,
    tools=[verify_plan_access],
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

from google.adk.apps.app import App

app = App(root_agent=root_agent, name="clientdata_accessplan_recomm_agent")
