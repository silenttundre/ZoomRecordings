import os, sys
from commons import get_directory_files, upload_to_google_drive


def main():
    # Example usage
    credentials_path = 'credentials.json'

    # Local directory with files to upload
    path = 'zoom2_recordings'
    files_to_upload = get_directory_files(path)

    # Specify the Google Drive folder name
    folder_name = 'zoom2_recordings'

    # First, create the folder in Google Drive or get its ID
    uploaded_files = upload_to_google_drive(
        credentials_path,
        files_to_upload,
        folder_name=folder_name  # New parameter to specify folder creation/selection
    )
    print(f"Total files uploaded: {len(uploaded_files)}")


if __name__ == "__main__":
    main()


