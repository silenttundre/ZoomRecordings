import os
import json
import requests
import io
import pytz
from datetime import datetime
from commons import (
    get_access_token,
    fetch_recordings
)
from constants import (
    ZOOM_2_CLIENT_ID,
    ZOOM_2_CLIENT_SECRET,
    ZOOM_2_TOKEN_URL,
    API_URL,
    COURSE_MAPPING_ZOOM2,
    DAY_OF_WEEK,
)
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError


def parse_time_range(time_str):
    """
    Parse a time range string into start and end datetime times

    Args:
        time_str (str): Time range in format '4:00pm - 6:19pm'

    Returns:
        tuple: (start_time, end_time) as datetime.time objects
    """
    import re
    from datetime import datetime, time

    # Remove any extra whitespace around the hyphen and split the time range
    time_str = time_str.replace(' ', '')
    time_pattern = r'(\d+):(\d+)(am|pm)-(\d+):(\d+)(am|pm)'
    match = re.match(time_pattern, time_str, re.IGNORECASE)

    if not match:
        raise ValueError(f"Unable to parse time range: {time_str}")

    start_hour, start_minute, start_meridiem, end_hour, end_minute, end_meridiem = match.groups()

    # Convert to 24-hour format
    start_hour = int(start_hour)
    end_hour = int(end_hour)

    # Handle start time AM/PM conversion
    if start_meridiem.lower() == 'pm' and start_hour != 12:
        start_hour += 12
    elif start_meridiem.lower() == 'am' and start_hour == 12:
        start_hour = 0

    # Handle end time AM/PM conversion
    if end_meridiem.lower() == 'pm' and end_hour != 12:
        end_hour += 12
    elif end_meridiem.lower() == 'am' and end_hour == 12:
        end_hour = 0

    start_time = time(start_hour, int(start_minute))
    end_time = time(end_hour, int(end_minute))

    return start_time, end_time


def get_mimetype(file_extension):
    """
    Determine mimetype based on file extension
    """
    mimetypes = {
        'mp4': 'video/mp4',
        'mp3': 'audio/mpeg',
        'txt': 'text/plain',
        'pdf': 'application/pdf',
        'mov': 'video/quicktime',
        'wav': 'audio/wav',
    }
    return mimetypes.get(file_extension.lower(), 'application/octet-stream')


def ensure_folder_exists(drive_service, parent_folder_name, subfolder_name):
    """
    Ensure a specific subfolder exists under a parent folder in Google Drive

    Args:
        drive_service: Google Drive service
        parent_folder_name (str): Name of the parent folder
        subfolder_name (str): Name of the subfolder to create/find

    Returns:
        str: Folder ID of the subfolder
    """
    # First, find the parent folder
    parent_results = drive_service.files().list(
        q=f"name='{parent_folder_name}' and mimeType='application/vnd.google-apps.folder'",
        spaces='drive'
    ).execute()
    parent_folders = parent_results.get('files', [])

    if not parent_folders:
        # Create parent folder if it doesn't exist
        parent_folder_metadata = {
            'name': parent_folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        parent_folder = drive_service.files().create(
            body=parent_folder_metadata,
            fields='id'
        ).execute()
        parent_folder_id = parent_folder.get('id')
        print(f"Created new parent folder: {parent_folder_name}")
    else:
        parent_folder_id = parent_folders[0]['id']

    # Now find or create the subfolder
    subfolder_results = drive_service.files().list(
        q=f"name='{subfolder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_folder_id}' in parents",
        spaces='drive'
    ).execute()
    subfolders = subfolder_results.get('files', [])

    if not subfolders:
        # Create subfolder
        subfolder_metadata = {
            'name': subfolder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        subfolder = drive_service.files().create(
            body=subfolder_metadata,
            fields='id'
        ).execute()
        subfolder_id = subfolder.get('id')
        print(f"Created new subfolder: {subfolder_name}")
    else:
        subfolder_id = subfolders[0]['id']

    return subfolder_id


def get_course_from_mapping(meeting_datetime):
    """
    Find matching course based on the meeting time and day

    Args:
        meeting_datetime (datetime): Datetime of the meeting

    Returns:
        str: Matching course folder name or None if no match found
    """
    meeting_time = meeting_datetime.time()
    meeting_day = meeting_datetime.strftime('%A')

    for course_name, course_info in COURSE_MAPPING_ZOOM2.items():
        try:
            # Check if the day exists in the course schedule
            if meeting_day not in course_info['schedule']:
                continue

            # Get times for this specific day
            day_times = course_info['schedule'][meeting_day]

            # Check time ranges for this day
            for time_range in day_times:
                # Parse time range
                start_time, end_time = parse_time_range(time_range)

                # Check if meeting time is within the course time range
                if start_time <= meeting_time <= end_time:
                    return course_info['folder_name']

        except ValueError as e:
            print(f"Error parsing time for {course_name}: {e}")

    return None


def get_meeting_participants(meeting_id, access_token):
    """
    Fetch participant information for a past meeting using Zoom Past Meeting API

    Args:
        meeting_id (str): The Zoom meeting ID
        access_token (str): Zoom access token

    Returns:
        int: Number of participants in the meeting
    """
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    try:
        # First get the past meeting instances
        instances_response = requests.get(
            f"{API_URL}/past_meetings/{meeting_id}/instances",
            headers=headers
        )
        instances_response.raise_for_status()
        instances_data = instances_response.json()

        total_participants = 0

        # If we have instances, check each one
        if instances_data.get('meetings', []):
            for instance in instances_data['meetings']:
                try:
                    # Get participants for this instance
                    participants_response = requests.get(
                        f"{API_URL}/past_meetings/{instance.get('uuid')}/participants",
                        headers=headers
                    )
                    participants_response.raise_for_status()
                    participants_data = participants_response.json()

                    # Count unique participants
                    unique_participants = set()
                    for participant in participants_data.get('participants', []):
                        identifier = participant.get('id') or participant.get('user_name')
                        if identifier:
                            unique_participants.add(identifier)

                    total_participants = max(total_participants, len(unique_participants))
                except requests.RequestException as e:
                    print(f"Error fetching participants for meeting instance {instance.get('uuid')}: {e}")
        else:
            # If no instances found, try the meeting ID directly
            try:
                participants_response = requests.get(
                    f"{API_URL}/past_meetings/{meeting_id}/participants",
                    headers=headers
                )
                participants_response.raise_for_status()
                participants_data = participants_response.json()

                unique_participants = set()
                for participant in participants_data.get('participants', []):
                    identifier = participant.get('id') or participant.get('user_name')
                    if identifier:
                        unique_participants.add(identifier)

                total_participants = len(unique_participants)
            except requests.RequestException as e:
                print(f"Error fetching participants for meeting {meeting_id}: {e}")

        return total_participants

    except requests.RequestException as e:
        print(f"Error fetching meeting instances for {meeting_id}: {e}")
        return 0


def download_and_upload_recordings(
        access_token,
        drive_service,
        min_size_mb=20
):
    """
    Download Zoom recordings directly to Google Drive with date, time, and course-based subfolders
    """
    # Fetch recordings
    user_id = 'me'
    recordings_data = fetch_recordings(user_id, access_token)

    uploaded_file_ids = []
    failed_uploads = []

    for meeting in recordings_data.get('meetings', []):
        # Parse the start time to create a date-based subfolder
        try:
            # Parse the start time from the meeting data
            start_time = meeting.get('start_time')
            if not start_time:
                print("No start time found for a meeting. Skipping.")
                continue

            # Get meeting ID and fetch participant count
            meeting_id = str(meeting.get('id'))  # Ensure it's a string
            if meeting_id:
                participant_count = get_meeting_participants(meeting_id, access_token)
                print(f"Meeting ID {meeting_id}: {participant_count} participants")
            else:
                print("No meeting ID found. Skipping participant count.")
                participant_count = 0

            # Convert to datetime object
            # Convert UTC to PST
            utc_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            meeting_datetime = utc_time.astimezone(pytz.timezone('US/Pacific'))
            #meeting_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))

            # Create parent folder with the year and then a subfolder for the months
            parent_folder_name = meeting_datetime.strftime('%Y courses')
            date_subfolder_name = meeting_datetime.strftime('%B Courses')

            # Get the meeting topic
            topic = meeting.get('topic', 'Unknown Meeting')

            # Initialize course-specific subfolder name
            course_subfolder_name = None

            # First, try to match by time
            course_subfolder_name = get_course_from_mapping(meeting_datetime)


            # If no time match, try to match by course name
            if not course_subfolder_name:
                for course_name, course_info in COURSE_MAPPING_ZOOM2.items():
                    if course_name in topic:
                        course_subfolder_name = course_info['folder_name']
                        break

            # If still no match, use a generic folder
            if not course_subfolder_name:
                course_subfolder_name = 'Others'

            # Create full path: Parent Folder > Date Folder > Course Folder
            date_folder_id = ensure_folder_exists(drive_service, parent_folder_name, date_subfolder_name)
            course_folder_id = ensure_folder_exists(drive_service, date_subfolder_name, course_subfolder_name)

            # Process each recording in the meeting
            for recording in meeting.get('recording_files', []):
                # Check file size
                file_size_mb = recording['file_size'] / (1024 * 1024)

                if file_size_mb >= min_size_mb:
                    # Prepare filename with topic and recording type
                    filename = f"{topic}_{recording['file_type']}_{meeting_datetime}.{recording['file_type']}"

                    # Download URL
                    download_url = recording['download_url']
                    headers = {"Authorization": f"Bearer {access_token}"}

                    try:
                        # Download the file
                        response = requests.get(download_url, headers=headers)
                        response.raise_for_status()

                        # Create an in-memory file-like object
                        file_content = io.BytesIO(response.content)

                        # Determine mimetype
                        mimetype = get_mimetype(recording['file_type'])

                        # Prepare file metadata for Google Drive
                        file_metadata = {
                            'name': filename,
                            'parents': [course_folder_id]
                        }

                        # # Upload directly to Google Drive
                        # media = MediaIoBaseUpload(
                        #     file_content,
                        #     mimetype=mimetype,
                        #     resumable=True
                        # )
                        #
                        # file = drive_service.files().create(
                        #     body=file_metadata,
                        #     media_body=media,
                        #     fields='id'
                        # ).execute()
                        #
                        # uploaded_file_ids.append(file.get('id'))
                        print(
                            f"Uploaded: {filename} to {date_subfolder_name}/{course_subfolder_name} (Size: {file_size_mb:.2f} MB)")

                    except requests.RequestException as e:
                        print(f"Error downloading {filename}: {e}")
                        failed_uploads.append((filename, "Download Error"))
                    except HttpError as e:
                        print(f"Error uploading {filename} to Google Drive: {e}")
                        failed_uploads.append((filename, "Upload Error"))
                    except Exception as e:
                        print(f"Unexpected error with {filename}: {e}")
                        failed_uploads.append((filename, "Unexpected Error"))

        except Exception as e:
            print(f"Error processing meeting: {e}")
            continue

    # Print summary of failed uploads
    if failed_uploads:
        print("\nFailed Uploads:")
        for filename, error_type in failed_uploads:
            print(f"{filename}: {error_type}")

    return uploaded_file_ids


def main():
    # Load credentials from JSON file
    with open('token.json', 'r') as token_file:
        token_info = json.load(token_file)

    # Reconstruct Google Drive credentials
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

    # Get Zoom access token
    access_token = get_access_token(
        ZOOM_2_CLIENT_ID,
        ZOOM_2_CLIENT_SECRET,
        ZOOM_2_TOKEN_URL
    )

    # Download and upload recordings
    uploaded_file_ids = download_and_upload_recordings(
        access_token,
        drive_service,
        min_size_mb=200
    )

    print(f"\nTotal recordings uploaded to Google Drive: {len(uploaded_file_ids)}")


if __name__ == "__main__":
    main()