from typing import Optional
from typing_extensions import Annotated
from pydantic import Field
from googleapiclient.errors import HttpError
from core.utils.logger import logger
from core.utils.state import global_state
from core.utils.env import EnvConfig
from app.middleware.google.GoogleAuthMiddleware import check_access
from core.utils.tools import doc_tag


def get_file_extension(mime_type: str) -> str:
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
        "application/vnd.google-apps.folder": "folder",
    }
    return mime_map.get(mime_type, "unknown")


@doc_tag("Drive")
def get_items_tool(
    folder_id: Annotated[
        Optional[str],
        Field(
            default=None,
            description="The ID of the folder to list items from. If not provided, lists items of the root directory.",
        ),
    ] = None,
) -> dict:
    """
    Lists all items in a specified Google Drive folder or the root directory if no folder_id is provided.

    Args:
    - folder_id (Optional[str]): The ID of the folder to list files and folders from.

    Returns:
    - dict: Contains file/folder data on success or error message on failure.
    """
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    service = global_state.get("google_drive_service")
    if service is None:
        logger.error("Google Drive service is not available in global state.")
        return {
            "status": "error",
            "error": f"Google Drive permission scope not available, please add this scope here: {EnvConfig.get('APP_HOST')}/auth/login",
        }

    try:
        query = f"'{folder_id}' in parents" if folder_id else "'root' in parents"
        results = (
            service.files()
            .list(q=query, pageSize=100, fields="files(id, name, mimeType)")
            .execute()
        )
        items = results.get("files", [])
        logger.info(
            f"Retrieved {len(items)} items from folder ID: {folder_id or 'root'}."
        )

        if not items:
            return {"status": "success", "data": []}

        item_list = [
            {
                "name": item["name"],
                "id": item["id"],
                "extension": get_file_extension(item["mimeType"]),
                "type": (
                    "folder"
                    if item["mimeType"] == "application/vnd.google-apps.folder"
                    else "file"
                ),
            }
            for item in items
        ]

        return {
            "status": "success",
            "data": item_list,
        }

    except HttpError as e:
        logger.error(f"Google API error: {e}")
        return {
            "status": "error",
            "google_error": {
                "code": e.resp.status,
                "message": e._get_reason(),
            },
        }

    except Exception as e:
        logger.error(f"Failed to retrieve items: {str(e)}")
        return {
            "status": "error",
            "error": f"Failed to retrieve items: {str(e)}",
        }
