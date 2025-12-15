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
