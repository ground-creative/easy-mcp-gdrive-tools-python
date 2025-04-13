from typing import List
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger
from core.utils.state import global_state
from core.utils.env import EnvConfig
from app.middleware.google.GoogleAuthMiddleware import check_access
from core.utils.tools import doc_tag, doc_name


@doc_tag("Spreadsheets")
@doc_name("Add rows to spreadsheet")
def gdrive_add_rows_to_sheet_tool(
    sheet_id: Annotated[
        str, Field(description="The ID of the sheet to add content to.")
    ],
    values: Annotated[
        List[List[str]],
        Field(
            description="A list of lists representing rows and columns of content to add."
        ),
    ],
) -> dict:
    """
    Adds content to an existing Google Sheets document.

    * Requires permission scope for spreadsheets.

    Args:
    - sheet_id (str): The ID of the sheet to add content to.
    - values (list): A list of lists representing rows and columns of content to add.

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

        # Specify the range where the content will be added (e.g., "Sheet1")
        range_name = "Sheet1"  # Adjust if necessary

        # Append the content to the sheet
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id, range=range_name, valueInputOption="RAW", body=body
        ).execute()

        logger.info(f"Successfully added content to sheet ID: {sheet_id}.")
        return {"status": "success", "message": "Content added successfully."}

    except Exception as e:
        logger.error(f"Failed to add content to sheet: {str(e)}")
        return {"status": "error", "error": f"{str(e)}"}
