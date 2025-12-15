import os

from dotenv import load_dotenv

load_dotenv()

import vertexai
from vertexai import agent_engines
from agent import root_agent

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
STAGING_BUCKET = "gs://datasets-ccibt-hack25ww7-711"

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)

# Wrap the agent in an AdkApp object
app = agent_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)

remote_app = agent_engines.create(
    agent_engine=app,
    requirements=[
        "google-cloud-aiplatform[adk,agent_engines]"   
    ]
)

print(f"Deployment finished!")
print(f"Resource Name: {remote_app.resource_name}")
