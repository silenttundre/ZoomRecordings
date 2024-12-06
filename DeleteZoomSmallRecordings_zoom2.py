from constants import ZOOM_2_CLIENT_ID, ZOOM_2_CLIENT_SECRET, ZOOM_2_TOKEN_URL, API_URL
from commons import get_tomorrow_date, get_access_token, fetch_recordings



# Main logic to find and delete recordings
def main():
    #test_auth("zoom2@cstu.edu")

    access_token = get_access_token(ZOOM_2_CLIENT_ID, ZOOM_2_CLIENT_SECRET, ZOOM_2_TOKEN_URL)

    #user_id = "zoom2@cstu.edu"
    user_id = "me"  # Replace with specific user ID or "me" for the authenticated account
    print("Access token: {}".format(access_token))

    print("Fetching recordings...")
    recordings_data = fetch_recordings(user_id, access_token)

    for meeting in recordings_data.get("meetings", []):
        id = meeting["id"]
        for recording in meeting.get("recording_files", []):
            meeting_id = recording["meeting_id"]
            file_size_mb = recording["file_size"] / (1024 * 1024)  # Convert bytes to MB
            print("meeting_id: {} - size: {}".format(meeting_id, file_size_mb))
            if file_size_mb < 2:  # Filter for recordings smaller than 2MB
                print(f"Deleting Meeting {meeting_id} (Size: {file_size_mb:.2f} MB)...")
                print(f"[* {meeting['topic']}: {meeting['start_time']} {meeting['timezone']} *]")
                #delete_recording(meeting_id, access_token)
            break

if __name__ == "__main__":
    main()