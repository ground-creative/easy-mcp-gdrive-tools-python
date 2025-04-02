import json
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state  # Import global state
from app.middleware.google.GoogleAuthMiddleware import check_access


def get_item_info_by_id_tool(file_id: str) -> str:
    """
    Retrieves information about a file or folder in Google Drive based on its ID.

    Args:
    - file_id (str): The ID of the file or folder to retrieve information from.

    Returns:
    - JSON string indicating success or error, along with the file/folder information.
    """

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve the Google Drive service from global state
    service = global_state.get("google_drive_service")
    if service is None:
        logger.error("Google Drive service is not available in global state.")
        return json.dumps(
            {"status": "error", "error": "Google Drive service is not initialized."}
        )

    try:
        logger.info(f"Attempting to retrieve information for ID: {file_id}")

        # Get the file metadata
        file_metadata = (
            service.files()
            .get(fileId=file_id, fields="id, name, mimeType, size, parents")
            .execute()
        )

        # Determine if it's a file or folder
        is_folder = (
            file_metadata.get("mimeType") == "application/vnd.google-apps.folder"
        )

        # Initialize file count
        file_count = 0

        # If it's a folder, count the files inside it
        if is_folder:
            query = f"'{file_id}' in parents"
            results = service.files().list(q=query, fields="files(id)").execute()
            file_count = len(results.get("files", []))

        logger.info(f"Successfully retrieved information for ID: {file_id}.")
        return json.dumps(
            {
                "status": "success",
                "file_info": file_metadata,
                "is_folder": is_folder,  # Indicate if it's a folder
                "file_count": file_count,  # Count of files inside the folder
            }
        )
    except Exception as e:
        logger.error(f"Failed to retrieve file information: {str(e)}")
        return json.dumps(
            {
                "status": "error",
                "error": f"Failed to retrieve file information: {str(e)}",
            }
        )
