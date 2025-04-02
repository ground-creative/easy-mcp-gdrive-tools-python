import json
from typing import Dict
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state  # Import global state
from app.middleware.google.GoogleAuthMiddleware import check_access


def create_drive_folder_tool(
    folder_name: Annotated[
        str, Field(description="The name of the folder to create. Ex: 'New Folder'")
    ],
    parent_id: Annotated[
        str,
        Field(
            description="The ID of the parent folder (optional). If None, creates in root. Ex: '1234567890abcdef'"
        ),
    ] = None,
) -> str:  # Change return type to str
    """
    Creates a new folder in Google Drive.

    Args:
    - folder_name (str): The name of the folder to create.
    - parent_id (str): The ID of the parent folder (optional). If None, creates in root.

    Returns:
    - JSON string containing the folder name and its corresponding ID on success.
    - JSON string with an error message on failure.

    Example Payload:
    {
        "folder_name": "New Folder",
        "parent_id": "1234567890abcdef"  # Optional
    }

    Example Response on Success:
    {
        "status": "success",
        "data": {
            "name": "New Folder",
            "id": "abcdef1234567890"
        }
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

    # Create the folder
    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }

    if parent_id:
        file_metadata["parents"] = [parent_id]  # Set parent folder ID if provided
        logger.debug(
            f"Creating subfolder '{folder_name}' under parent ID '{parent_id}'."
        )
    else:
        logger.debug(f"Creating root folder '{folder_name}'.")

    try:
        folder = service.files().create(body=file_metadata, fields="id").execute()
        logger.info(
            f"Successfully created folder '{folder_name}' with ID: {folder.get('id')}."
        )
        return json.dumps(
            {
                "status": "success",
                "data": {"name": folder_name, "id": folder.get("id")},
            }
        )
    except Exception as e:
        logger.error(f"Failed to create folder: {str(e)}")
        return json.dumps(
            {
                "status": "error",
                "error": f"Failed to create folder: {str(e)}",
            }
        )
