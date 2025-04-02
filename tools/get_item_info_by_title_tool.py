import json
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state  # Import global state
from app.middleware.google.GoogleAuthMiddleware import check_access


def search_files_by_title_tool(
    title: Annotated[str, Field(description="The title of the files to search for.")],
) -> str:
    """
    Searches for files and folders in Google Drive by their title.

    Args:
    - title (str): The title of the files or folders to search for.

    Returns:
    - JSON string containing the list of matching files or folders or an error message.
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
        # Construct the query to search for files and folders by title
        query = f"name='{title}'"

        # Execute the search
        results = (
            service.files()
            .list(q=query, fields="files(id, name, mimeType, parents)")
            .execute()
        )

        items = results.get("files", [])

        if not items:
            logger.info(f"No files or folders found with title: {title}.")
            return json.dumps({"status": "success", "files": []})

        logger.info(f"Found {len(items)} item(s) with title: {title}.")
        return json.dumps({"status": "success", "files": items})
    except Exception as e:
        logger.error(f"Failed to search for items: {str(e)}")
        return json.dumps(
            {"status": "error", "error": f"Failed to search for items: {str(e)}"}
        )  # JSON-compatible error response
