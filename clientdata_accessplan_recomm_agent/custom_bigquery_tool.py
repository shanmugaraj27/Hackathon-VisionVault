from google.cloud import bigquery
from typing import Dict, Any


class BigQueryCustomTool:
    """Custom tool to fetch user data from BigQuery"""
    
    def __init__(self, project_id: str, dataset_id: str, table_id: str):
        """
        Initialize the custom BigQuery tool
        
        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset ID
            table_id: BigQuery table ID
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.client = bigquery.Client(project=project_id)
    
    def fetch_user_record(self, user_id: str) -> Dict[str, Any]:
        """
        Fetch a user record from BigQuery and return username and plan.
        
        Args:
            user_id: The user ID to fetch
            
        Returns:
            Dictionary with username and Plan
        """
        query = f"""
        SELECT `User ID`, `Plan`
        FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        WHERE `User ID` = @user_id
        LIMIT 1
        """
        print ("Executing user:",user_id)
        print ("Executing query:", query)
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("user_id", "STRING", user_id)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        for row in results:
            return {
                "username": row['User ID'],
                "plan": row['Plan']
            }
        
        return {"username": None, "plan": None}
    
    def update_user_plan(self, user_id: str, new_plan: str) -> Dict[str, Any]:
        """
        Update a user's plan in BigQuery.
        
        Args:
            user_id: The user ID to update
            new_plan: The new plan name (Gold, Silver, Bronze)
            
        Returns:
            Dictionary with status and message
        """
        # Validate plan name
        valid_plans = ['Gold', 'Silver', 'Bronze']
        if new_plan not in valid_plans:
            return {
                "success": False,
                "message": f"Invalid plan: {new_plan}. Valid plans are: {', '.join(valid_plans)}"
            }
        
        query = f"""
        UPDATE `{self.project_id}.{self.dataset_id}.{self.table_id}`
        SET `Plan` = @new_plan
        WHERE `User ID` = @user_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("new_plan", "STRING", new_plan),
                bigquery.ScalarQueryParameter("user_id", "STRING", user_id)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()  # Wait for the query to complete
            
            return {
                "success": True,
                "message": f"Successfully updated user {user_id} plan to {new_plan}",
                "user_id": user_id,
                "new_plan": new_plan
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error updating plan: {str(e)}"
            }
