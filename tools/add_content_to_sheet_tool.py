import json
from typing import List
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state  # Import global state
from app.middleware.google.GoogleAuthMiddleware import check_access


def add_content_to_google_sheet_tool(
    sheet_id: Annotated[
        str, Field(description="The ID of the sheet to add content to.")
    ],
    values: Annotated[
        List[List[str]],
        Field(
            description="A list of lists representing rows and columns of content to add."
        ),
    ],
) -> str:
    """
    Adds content to an existing Google Sheets document.

    Args:
    - sheet_id (str): The ID of the sheet to add content to.
    - values (list): A list of lists representing rows and columns of content to add.

    Returns:
    - JSON string indicating success or error.
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

        # Specify the range where the content will be added (e.g., "Sheet1")
        range_name = "Sheet1"  # Adjust as necessary

        # Append the sheet with the new content
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id, range=range_name, valueInputOption="RAW", body=body
        ).execute()

        logger.info(f"Successfully added content to sheet ID: {sheet_id}.")
        return json.dumps(
            {"status": "success", "message": "Content added successfully."}
        )
    except Exception as e:
        logger.error(f"Failed to add content to sheet: {str(e)}")
        return json.dumps(
            {"status": "error", "error": f"Failed to add content to sheet: {str(e)}"}
        )  # JSON-compatible error response
