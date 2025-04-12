from typing import List
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger
from core.utils.state import global_state
from core.utils.env import EnvConfig
from app.middleware.google.GoogleAuthMiddleware import check_access
from core.utils.tools import doc_tag


@doc_tag("Sheets")
def edit_rows_tool(
    sheet_id: Annotated[
        str, Field(description="The ID of the sheet to edit content in.")
    ],
    range_name: Annotated[
        str, Field(description="The range of cells to edit (e.g., 'Sheet1!A1:B2').")
    ],
    values: Annotated[
        List[List[str]],
        Field(
            description="A list of lists representing the new content to replace existing content."
        ),
    ],
) -> dict:
    """
    Edits rows in an existing Google Sheets document.

    Args:
    - sheet_id (str): The ID of the sheet to edit content in.
    - range_name (str): The range of cells to edit (e.g., 'Sheet1!A1:B2').
    - values (list): A list of lists representing the new content to replace existing content.

    Returns:
    - Dictionary indicating success or error.
    """

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve the Google Sheets service from global state
    service = global_state.get("google_sheets_service")
    if service is None:
        logger.error("Google Sheets service is not available in global state.")
        return {
            "status": "error",
            "error": f"Google Sheets permission scope not available, please add this scope here: {EnvConfig.get('APP_HOST')}/auth/login",
        }

    try:
        # Prepare the request body
        body = {"values": values}

        # Update the sheet with the new content
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption="RAW",
            body=body,
        ).execute()

        logger.info(f"Successfully edited content in sheet ID: {sheet_id}.")
        return {
            "status": "success",
            "message": "Content edited successfully.",
        }

    except Exception as e:
        logger.error(f"Failed to edit content in sheet: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
        }
