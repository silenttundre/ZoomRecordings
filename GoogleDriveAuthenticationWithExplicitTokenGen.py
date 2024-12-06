import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate(credentials_path='credentials.json'):
    """
    Authenticate and generate a token with all required fields
    """
    # Load client configuration
    with open(credentials_path, 'r') as f:
        client_config = json.load(f)

    # Initialize the OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(
        credentials_path,
        scopes=SCOPES
    )

    # Run local server for authentication
    credentials = flow.run_local_server(port=0)

    # Prepare token dictionary with all required fields
    token_dict = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': client_config['installed']['token_uri'],
        'client_id': client_config['installed']['client_id'],
        'client_secret': client_config['installed']['client_secret'],
        'scopes': SCOPES,
        'expiry': credentials.expiry.isoformat() if credentials.expiry else None
    }

    # Save the complete token
    with open('token.json', 'w') as f:
        json.dump(token_dict, f)

    print("Authentication successful. Token saved as token.json")

def main():
    authenticate()

if __name__ == "__main__":
    main()