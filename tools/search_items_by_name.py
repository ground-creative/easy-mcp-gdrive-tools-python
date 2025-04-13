from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger
from core.utils.state import global_state
from core.utils.env import EnvConfig
from app.middleware.google.GoogleAuthMiddleware import check_access
from core.utils.tools import doc_tag, doc_name


@doc_tag("Drive")
@doc_name("Search items by name")
def gdrive_search_items_by_name_tool(
    name: Annotated[str, Field(description="The name of the files to search for.")],
) -> dict:
    """
    Searches for files and folders in Google Drive by their name.

    * Requires permission scope for the drive.

    Args:
    - name (str): The name of the files or folders to search for.

    Returns:
    - Dictionary containing the list of matching files or folders or an error message.
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

    try:
        # Construct the query to search for files and folders by name
        query = f"name='{name}'"

        # Execute the search
        results = (
            service.files()
            .list(q=query, fields="files(id, name, mimeType, parents)")
            .execute()
        )

        items = results.get("files", [])

        if not items:
            logger.info(f"No files or folders found with name: {name}.")
            return {"status": "success", "files": []}

        logger.info(f"Found {len(items)} item(s) with name: {name}.")
        return {"status": "success", "files": items}

    except Exception as e:
        logger.error(f"Failed to search for items: {str(e)}")
        return {"status": "error", "error": f"{str(e)}"}
