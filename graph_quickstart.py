import sys
import json
import logging

import requests
import msal
#link     https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-v2-python-daemon
def main(data):
    cred_file = data['data']['json_file']
    config = json.load(open(cred_file))

    app = msal.ConfidentialClientApplication(
        config["client_id"], authority=config["authority"],
        client_credential=config["secret"],

    )

    result = None

    result = app.acquire_token_silent(config["scope"], account=None)

    if not result:
        logging.info("No suitable token exists in cache. Let's get a new one from AAD.")
        result = app.acquire_token_for_client(scopes=config["scope"])

    if "access_token" in result:

        graph_data = requests.get(
            config["endpoint"],
            headers={'Authorization': 'Bearer ' + result['access_token']}, ).json()
        print("Graph API call result: ")
        print(json.dumps(graph_data, indent=2))
    else:
        print(result.get("error"))
        print(result.get("error_description"))
        print(result.get("correlation_id"))
