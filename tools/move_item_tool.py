import json
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state  # Import global state
from app.middleware.google.GoogleAuthMiddleware import check_access


def move_item_tool(item_id: str, new_parent_id: str) -> str:
    """
    Moves a file or folder to a new folder in Google Drive.

    Args:
    - item_id (str): The ID of the file or folder to move.
    - new_parent_id (str): The ID of the new parent folder.

    Returns:
    - JSON string indicating success or error.
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
        logger.info(
            f"Attempting to move item ID: {item_id} to new parent ID: {new_parent_id}"
        )

        # Retrieve the current parents of the item
        item_metadata = service.files().get(fileId=item_id, fields="parents").execute()
        current_parents = item_metadata.get("parents", [])

        # Move the item by updating its parents
        if current_parents:
            # Remove the item from its current parents
            service.files().update(
                fileId=item_id,
                removeParents=",".join(current_parents),
                addParents=new_parent_id,
                fields="id, parents",
            ).execute()

        logger.info(
            f"Successfully moved item ID: {item_id} to new parent ID: {new_parent_id}."
        )
        return json.dumps(
            {
                "status": "success",
                "message": f"Item ID: {item_id} moved to folder ID: {new_parent_id}.",
            }
        )
    except Exception as e:
        logger.error(f"Failed to move item: {str(e)}")
        return json.dumps(
            {
                "status": "error",
                "error": f"Failed to move item: {str(e)}",
            }
        )
