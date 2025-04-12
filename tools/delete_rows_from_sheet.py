from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger
from core.utils.state import global_state
from core.utils.env import EnvConfig
from app.middleware.google.GoogleAuthMiddleware import check_access
from core.utils.tools import doc_tag


@doc_tag("Sheets")
def delete_rows_tool(
    sheet_id: Annotated[
        str, Field(description="The ID of the sheet from which to delete rows.")
    ],
    row_indices: Annotated[
        list, Field(description="A list of row indices to delete (1-based).")
    ],
) -> dict:
    """
    Deletes specified rows from an existing Google Sheets document.

    Args:
    - sheet_id (str): The ID of the sheet from which to delete rows.
    - row_indices (list): A list of row indices (1-based) to delete.

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
        # Get the sheet ID (numeric) from the spreadsheet
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheet_id_numeric = spreadsheet["sheets"][0]["properties"][
            "sheetId"
        ]  # First sheet

        # Prepare the requests for deleting rows
        requests = []
        for row_index in sorted(row_indices, reverse=True):  # Reverse to avoid shifting
            requests.append(
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id_numeric,
                            "dimension": "ROWS",
                            "startIndex": row_index - 1,
                            "endIndex": row_index,
                        }
                    }
                }
            )

        # Execute the batch update request
        body = {"requests": requests}
        service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body).execute()

        logger.info(
            f"Successfully deleted rows {row_indices} from sheet ID: {sheet_id}."
        )
        return {
            "status": "success",
            "message": f"Rows {row_indices} deleted successfully.",
        }

    except Exception as e:
        logger.error(f"Failed to delete rows from sheet: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
        }
