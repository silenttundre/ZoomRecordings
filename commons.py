# Common functions
import json
import os
import requests
import base64
from constants import API_URL
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def get_directory_files(directory_path):
    """
    Returns a list of files in the specified directory.

    Args:
        directory_path (str): Path to the directory

    Returns:
        list: Full file paths of files in the directory
    """
    try:
        # Get full file paths, filtering out directories
        files = [
            os.path.join(directory_path, file)
            for file in os.listdir(directory_path)
            if os.path.isfile(os.path.join(directory_path, file))
        ]
        return files
    except Exception as e:
        print(f"Error reading directory: {e}")
        return []

def get_tomorrow_date():
    """
    The tommorrow date
    :return: str in yyyy-mm-dd format
    """
    # Get the current date and add one day
    next_day = datetime.now() + timedelta(days=1)

    return next_day.strftime("%Y-%m-%d")

def get_current_date():
    """
    The current date
    :return:  str in yyyy-mm-dd format
    """
    # Get the current date and add one day
    today = datetime.now()

    return today.strftime("%Y-%m-%d")

#===============================================
# Zoom functions
#===============================================
# Generate an access token (OAuth)
def get_access_token(clientID, clientSecret, tokenUrl):
    """
    Retrieve the Zoom access token
    :return:
    """
    auth_header = f"{clientID}:{clientSecret}"
    #print(auth_header)
    auth_header = base64.b64encode(f"{clientID}:{clientSecret}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    #print(headers)
    data = {"grant_type": "account_credentials"}
    response = requests.post(tokenUrl, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# Fetch cloud recordings for a user
def fetch_recordings(user_id, access_token):
    # Call the function and store the result
    formatted_current_date = get_tomorrow_date()
    print("Current date: {}".format(formatted_current_date))
    url = f"{API_URL}/users/{user_id}/recordings"
    params = { "from": "2024-12-01", "to": formatted_current_date,"page_size": 30}
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


# Delete a specific recording
def delete_recording(meeting_id, access_token):
    url = f"{API_URL}/meetings/{meeting_id}/recordings?action=trash"

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        print(f"Recording {meeting_id} deleted successfully.")
    elif response.status_code == 404:
        print(f"Recording not found: {meeting_id}. It may have already been deleted.")
        print(f"Full response: {response.text}")
        return False
    else:
        print(f"Failed to delete recording {meeting_id}. Status code: {response.status_code}")

def download_large_recordings(
        access_token,
        min_size_mb=20,
        download_dir='zoom_recordings'
):
    """
    Download Zoom recordings larger than specified size

    Args:
        access_token (str): Zoom API access token
        min_size_mb (int): Minimum file size to download in MB
        download_dir (str): Directory to save downloaded recordings

    Returns:
        list: Paths of downloaded recordings
    """
    # Create download directory if it doesn't exist
    os.makedirs(download_dir, exist_ok=True)

    # Fetch recordings
    user_id = 'me'
    recordings_data = fetch_recordings(user_id, access_token)

    downloaded_files = []

    for meeting in recordings_data.get('meetings', []):
        for recording in meeting.get('recording_files', []):
            # Check file size
            file_size_mb = recording['file_size'] / (1024 * 1024)

            if file_size_mb >= min_size_mb:
                # Prepare filename
                filename = f"{meeting['id']}_{recording['id']}.{recording['file_type']}"
                filepath = os.path.join(download_dir, filename)

                # Download file
                download_url = recording['download_url']
                headers = {"Authorization": f"Bearer {access_token}"}

                response = requests.get(download_url, headers=headers)

                with open(filepath, 'wb') as f:
                    f.write(response.content)

                downloaded_files.append(filepath)
                print(f"Downloaded: {filename} (Size: {file_size_mb:.2f} MB)")

    return downloaded_files

#=====================================
# Google functions
#=====================================
def upload_to_google_drive(
        credentials_path,
        files_to_upload,
        folder_name=None
):
    """
    Upload files to Google Drive, optionally to a specified folder

    Args:
        credentials_path (str): Path to Google OAuth credentials file
        files_to_upload (list): List of file paths to upload
        folder_name (str, optional): Name of folder to upload files to in Google Drive

    Returns:
        list: File IDs of uploaded files
    """

    # Load credentials from JSON file
    with open('token.json', 'r') as token_file:
        token_info = json.load(token_file)

    # Reconstruct credentials
    creds = Credentials(
        token=token_info['token'],
        refresh_token=token_info['refresh_token'],
        token_uri=token_info['token_uri'],
        client_id=token_info['client_id'],
        client_secret=token_info['client_secret'],
        scopes=token_info['scopes']
    )

    # Build Google Drive service
    drive_service = build('drive', 'v3', credentials=creds)

    # If folder_name is provided, find or create the folder
    folder_id = None
    if folder_name:
        # Check if folder already exists
        results = drive_service.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
            spaces='drive'
        ).execute()

        folders = results.get('files', [])

        if not folders:
            # Create the folder if it doesn't exist
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = drive_service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            folder_id = folder.get('id')
            print(f"Created new folder: {folder_name}")
        else:
            # Use the existing folder
            folder_id = folders[0]['id']
            print(f"Using existing folder: {folder_name}")

    uploaded_file_ids = []
    for file_path in files_to_upload:
        file_metadata = {
            'name': os.path.basename(file_path)
        }

        # Add folder_id if specified
        if folder_id:
            file_metadata['parents'] = [folder_id]

        media = MediaFileUpload(file_path)

        # Upload file
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        uploaded_file_ids.append(file.get('id'))
        print(f"Uploaded: {os.path.basename(file_path)} to Google Drive")

    return uploaded_file_ids