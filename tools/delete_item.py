import base64
import time
from typing import Optional
from typing_extensions import Annotated
from pydantic import Field
from googleapiclient.errors import HttpError
from core.utils.logger import logger
from core.utils.state import global_state
from core.utils.env import EnvConfig
from app.middleware.google.GoogleAuthMiddleware import check_access
from core.utils.tools import doc_tag, doc_name

# Define the validity duration for the confirmation token (in seconds)
CONFIRMATION_TOKEN_VALIDITY_DURATION = 5 * 60  # 5 minutes


@doc_tag("Drive")
@doc_name("Delete item")
def gdrive_delete_item_tool(
    file_id: Annotated[
        str, Field(description="The ID of the file or folder to delete.")
    ],
    confirmation_token: Annotated[
        Optional[str],
        Field(
            description="An optional token to confirm the deletion. "
            "If not provided, a token will be generated based on the file/folder ID. "
            "This token must be used to confirm the deletion request."
        ),
    ] = None,
) -> dict:
    """
    Deletes a specified item (file or folder) from Google Drive with confirmation logic.

    * Requires permission scope for the drive.

    The function first checks if a confirmation token is provided.
    If not, it generates a token based on the item ID.
    The user must then confirm the deletion using this token.
    If the token is provided, the function validates it before proceeding with the deletion.
    The token is valid for a specified duration.

    Args:
    - file_id (str): The ID of the file or folder to delete.
    - confirmation_token (Optional[str]): An optional token to confirm the deletion. If not provided, a token will be generated based on the file/folder ID.

    Returns:
    - dict: Dictionary indicating success or error.
    """

    logger.info(
        f"Request received to delete item with ID '{file_id}' and confirmation token: {confirmation_token}"
    )

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve the Google Drive service from global state
    drive_service = global_state.get("google_drive_service")
    if drive_service is None:
        logger.error("Google Drive service is not available in global state.")
        return {
            "status": "error",
            "error": f"Google Drive permission scope not available, please add this scope here: {EnvConfig.get('APP_HOST')}/auth/login",
        }

    # Generate a confirmation token if not provided
    if not confirmation_token:
        # Create a string with the request parameters and current timestamp
        params_string = f"{file_id}:{int(time.time())}"
        confirmation_token = base64.b64encode(params_string.encode()).decode()
        logger.info(f"Generated confirmation token: {confirmation_token}")
        return {
            "message": f"Confirmation required to delete item with ID '{file_id}'. Confirm deletion with user and use the given confirmation_token with the same request parameters.",
            "confirmation_token": confirmation_token,
            "action": "confirm_deletion",
        }

    # Decode and validate the confirmation token
    try:
        decoded_params = base64.b64decode(confirmation_token).decode()
        token_file_id, token_timestamp = decoded_params.split(":")
        token_timestamp = int(token_timestamp)

        # Check if the token has expired
        if time.time() - token_timestamp > CONFIRMATION_TOKEN_VALIDITY_DURATION:
            return {
                "error": "Confirmation token has expired. Please request a new token."
            }

        # Check if the parameters match
        if token_file_id != file_id:
            return {
                "error": "Invalid confirmation token. Parameters do not match, please request a new token.",
                "details": {
                    "token_params": {
                        "file_id": token_file_id,
                    },
                    "request_params": {
                        "file_id": file_id,
                    },
                },
            }

    except Exception as e:
        logger.error(f"Failed to decode confirmation token: {e}")
        return {"error": "Invalid confirmation token."}

    # Prepare to delete the item
    try:
        drive_service.files().delete(fileId=file_id).execute()
        logger.info(f"Successfully deleted item with ID: {file_id}")
        return {"status": "success", "message": "Item deleted successfully."}
    except HttpError as e:
        try:
            error_content = (
                e.error_details[0].get("message") if e.error_details else str(e)
            )
        except Exception:
            error_content = str(e)
        logger.error(
            f"Google Drive API error while deleting item {file_id}: {error_content}"
        )
        return {"status": "error", "error": error_content}
    except Exception as e:
        logger.error(f"Unexpected error while deleting item {file_id}: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}
