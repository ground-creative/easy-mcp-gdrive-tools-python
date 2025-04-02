import json
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state  # Import global state
from app.middleware.google.GoogleAuthMiddleware import check_access


def delete_file_tool(
    file_id: Annotated[str, Field(description="The ID of the file to delete.")],
) -> str:  # Change return type to str
    """
    Deletes a file from Google Drive.

    Args:
    - file_id (str): The ID of the file to delete.

    Returns:
    - JSON string indicating success or error.

    Example Response on Success:
    {
        "status": "success",
        "message": "File deleted successfully."
    }
    """

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response
    # Retrieve the Google Drive service from global state
    drive_service = global_state.get("google_drive_service")
    if drive_service is None:
        logger.error("Google Drive service is not available in global state.")
        return json.dumps(
            {"status": "error", "error": "Google Drive service is not initialized."}
        )

    try:
        # Delete the file
        drive_service.files().delete(fileId=file_id).execute()
        logger.info(f"Successfully deleted file with ID: {file_id}.")
        return json.dumps(
            {"status": "success", "message": "File deleted successfully."}
        )
    except Exception as e:
        logger.error(f"Failed to delete file: {str(e)}")
        return json.dumps(
            {"status": "error", "error": f"Failed to delete file: {str(e)}"}
        )  # JSON-compatible error response
