import os
import requests
from constants import (
    ZOOM_2_CLIENT_ID,
    ZOOM_2_CLIENT_SECRET,
    ZOOM_2_TOKEN_URL,
    API_URL
)
from commons import get_access_token, fetch_recordings, download_large_recordings


def main():
    # Get access token
    access_token = get_access_token(
        ZOOM_2_CLIENT_ID,
        ZOOM_2_CLIENT_SECRET,
        ZOOM_2_TOKEN_URL
    )

    # Download recordings 20MB or larger
    downloaded_files = download_large_recordings(access_token, min_size_mb=20, download_dir="zoom2_recordings")
    print(f"Total files downloaded: {len(downloaded_files)}")


if __name__ == "__main__":
    main()