from typing import Dict, Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger
from core.utils.state import global_state
from core.utils.env import EnvConfig
from app.middleware.google.GoogleAuthMiddleware import check_access
from core.utils.tools import doc_tag, doc_name


@doc_tag("Drive")
@doc_name("Create folder")
def gdrive_create_folder_tool(
    folder_name: Annotated[
        str, Field(description="The name of the folder to create. Ex: 'New Folder'")
    ],
    parent_id: Annotated[
        Optional[str],
        Field(
            description="The ID of the parent folder (optional). If None, creates in root. Ex: '1234567890abcdef'"
        ),
    ] = None,
) -> dict:
    """
    Creates a new folder in Google Drive.

    * Requires permission scope for the drive.

    Args:
    - folder_name (str): The name of the folder to create.
    - parent_id (str): The ID of the parent folder (optional). If None, creates in root.

    Returns:
    - dict: Dictionary containing the folder name and its corresponding ID on success, or error message on failure.
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
            "error": f"Google Drive permission scope not available, please add this scope here: {EnvConfig.get('APP_HOST')}/auth/login",
        }

    # Create the folder metadata
    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }

    if parent_id:
        file_metadata["parents"] = [parent_id]
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
        return {
            "status": "success",
            "data": {"name": folder_name, "id": folder.get("id")},
        }
    except Exception as e:
        logger.error(f"Failed to create folder: {str(e)}")
        return {
            "status": "error",
            "error": str(e),  # Return raw error string from Google API
        }
