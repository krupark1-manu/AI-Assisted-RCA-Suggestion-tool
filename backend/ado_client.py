import requests
import base64
from config.settings import ADO_ORG, ADO_PROJECT, ADO_PAT

def get_bug(bug_id):
    """Fetch a single bug from Azure DevOps"""
    url = f"{ADO_ORG}/{ADO_PROJECT}/_apis/wit/workitems/{bug_id}?api-version=7.0"

    AUTH_TOKEN = base64.b64encode(f":{ADO_PAT}".encode()).decode()
    HEADERS = {"Authorization": f"Basic {AUTH_TOKEN}"}

    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        return r.json()
    else:
        raise Exception(f"Error fetching bug ID: {bug_id}: {r.text}")
