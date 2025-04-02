import json
from typing import Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state  # Import global state
from app.middleware.google.GoogleAuthMiddleware import check_access


def get_file_extension(mime_type: str) -> str:
    """Map MIME type to file extension."""
    mime_map = {
        "application/pdf": "pdf",
        "text/plain": "txt",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/msword": "doc",
        "application/vnd.google-apps.document": "gdoc",
        "application/vnd.google-apps.spreadsheet": "gsheet",
        "application/vnd.google-apps.presentation": "gslides",
        "image/jpeg": "jpg",
        "image/png": "png",
        "application/vnd.google-apps.folder": "folder",  # For folders
        # Add more MIME types and extensions as needed
    }
    return mime_map.get(mime_type, "unknown")  # Default to 'unknown' if not found


def list_folder_contents_tool(
    folder_id: Annotated[
        Optional[str],
        Field(
            description="The ID of the folder to list contents from. If not provided, lists contents of the root directory."
        ),
    ],
) -> str:  # Change return type to str
    """
    Lists all files and folders in a specified Google Drive folder or the root directory if no folder_id is provided.

    Args:
    - folder_id (str, optional): The ID of the folder to list files and folders from.

    Returns:
    - JSON string containing file and folder names, their corresponding IDs, and extensions on success.
    - JSON string with an error message on failure.
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
        # Query to list all items (files and folders) in the specified folder or root directory
        if folder_id:
            query = f"'{folder_id}' in parents"
        else:
            query = "'root' in parents"  # List items in the root directory

        results = (
            service.files()
            .list(q=query, pageSize=100, fields="files(id, name, mimeType)")
            .execute()
        )
        items = results.get("files", [])
        logger.info(
            f"Retrieved {len(items)} items from folder ID: {folder_id if folder_id else 'root'}."
        )

        # Return empty list if no items found
        if not items:
            logger.info("No items found in the specified folder.")
            return json.dumps({"status": "success", "data": []})

        # Structure the response
        item_list = [
            {
                "name": item["name"],
                "id": item["id"],
                "extension": get_file_extension(
                    item["mimeType"]
                ),  # Get file/folder extension
                "type": (
                    "folder"
                    if item["mimeType"] == "application/vnd.google-apps.folder"
                    else "file"
                ),  # Indicate type
            }
            for item in items
        ]
        logger.debug(f"Items retrieved: {item_list}")

        return json.dumps(
            {
                "status": "success",
                "data": item_list,  # Ensure this is a JSON-compatible structure
            }
        )
    except Exception as e:
        logger.error(f"Failed to retrieve items: {str(e)}")
        return json.dumps(
            {
                "status": "error",
                "error": f"Failed to retrieve items: {str(e)}",
            }
        )  # JSON-compatible error response
