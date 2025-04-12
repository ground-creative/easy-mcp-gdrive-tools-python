from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state  # Import global state
from app.middleware.google.GoogleAuthMiddleware import check_access
from core.utils.tools import doc_tag
from core.utils.env import EnvConfig  # Assuming EnvConfig is available here


@doc_tag("Drive")
def get_item_details_tool(item_id: str) -> dict:
    """
    Retrieves information about a file or folder in Google Drive based on its ID.

    Args:
    - item_id (str): The ID of the file or folder to retrieve information from.

    Returns:
    - dict indicating success or error, along with the file/folder information.
    """

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve the Google Drive service from global state
    service = global_state.get("google_drive_service")
    if service is None:
        logger.error("Google Drive service is not available in global state.")
        return {
            "status": "error",
            "error": f"Google Drive permission scope not available. Please add this scope here: {EnvConfig.get('APP_HOST')}/auth/login",
        }

    try:
        logger.info(f"Attempting to retrieve information for ID: {item_id}")

        # Get the file metadata
        file_metadata = (
            service.files()
            .get(fileId=item_id, fields="id, name, mimeType, size, parents")
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
            query = f"'{item_id}' in parents"
            results = service.files().list(q=query, fields="files(id)").execute()
            file_count = len(results.get("files", []))

        logger.info(f"Successfully retrieved information for ID: {item_id}.")
        return {
            "status": "success",
            "file_info": file_metadata,
            "is_folder": is_folder,
            "file_count": file_count,
        }

    except Exception as e:
        logger.error(f"Failed to retrieve file information: {str(e)}")
        return {
            "status": "error",
            "error": str(e),  # Google API error is typically informative here
        }
