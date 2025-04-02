import json
from typing import Dict
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state  # Import global state
from app.middleware.google.GoogleAuthMiddleware import check_access


def delete_drive_folder_tool(
    folder_id: Annotated[
        str, Field(description="The ID of the folder to delete. Ex: 'abcdef1234567890'")
    ],
) -> str:  # Change return type to str
    """
    Deletes a folder in Google Drive.

    Args:
    - folder_id (str): The ID of the folder to delete.

    Returns:
    - JSON string indicating success or error.

    Example Response on Success:
    {
        "status": "success",
        "message": "Folder deleted successfully."
    }
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
        # Call the Drive API to delete the folder
        service.files().delete(fileId=folder_id).execute()
        logger.info(f"Successfully deleted folder with ID: {folder_id}.")
        return json.dumps(
            {"status": "success", "message": "Folder deleted successfully."}
        )
    except Exception as e:
        logger.error(f"Failed to delete folder: {str(e)}")
        return json.dumps(
            {"status": "error", "error": f"Failed to delete folder: {str(e)}"}
        )  # JSON-compatible error response
