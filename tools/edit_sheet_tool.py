import json
from typing import List
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state  # Import global state
from app.middleware.google.GoogleAuthMiddleware import check_access


def edit_content_in_google_sheet_tool(
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
) -> str:
    """
    Edits content in an existing Google Sheets document.

    Args:
    - sheet_id (str): The ID of the sheet to edit content in.
    - range_name (str): The range of cells to edit (e.g., 'Sheet1!A1:B2').
    - values (list): A list of lists representing the new content to replace existing content.

    Returns:
    - JSON string indicating success or error.

    Example Response on Success:
    {
        "status": "success",
        "message": "Content edited successfully."
    }
    """

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve the Google Sheets service from global state
    service = global_state.get("google_sheets_service")
    if service is None:
        logger.error("Google Sheets service is not available in global state.")
        return json.dumps(
            {"status": "error", "error": "Google Sheets service is not initialized."}
        )

    try:
        # Prepare the request body
        body = {"values": values}

        # Update the sheet with the new content
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id, range=range_name, valueInputOption="RAW", body=body
        ).execute()

        logger.info(f"Successfully edited content in sheet ID: {sheet_id}.")
        return json.dumps(
            {"status": "success", "message": "Content edited successfully."}
        )
    except Exception as e:
        logger.error(f"Failed to edit content in sheet: {str(e)}")
        return json.dumps(
            {"status": "error", "error": f"Failed to edit content in sheet: {str(e)}"}
        )  # JSON-compatible error response
