import json
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state  # Import global state
from app.middleware.google.GoogleAuthMiddleware import check_access


def delete_rows_from_google_sheet_tool(
    sheet_id: Annotated[
        str, Field(description="The ID of the sheet from which to delete rows.")
    ],
    row_indices: Annotated[
        list, Field(description="A list of row indices to delete (1-based).")
    ],
) -> str:
    """
    Deletes specified rows from an existing Google Sheets document.

    Args:
    - sheet_id (str): The ID of the sheet from which to delete rows.
    - row_indices (list): A list of row indices (1-based) to delete.

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
        # Get the sheet ID (numeric) from the spreadsheet
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheet_id_numeric = spreadsheet["sheets"][0]["properties"][
            "sheetId"
        ]  # Assuming you want the first sheet

        # Prepare the requests for deleting rows
        requests = []
        for row_index in sorted(
            row_indices, reverse=True
        ):  # Sort in reverse order to avoid index shifting
            requests.append(
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id_numeric,  # Use the numeric sheet ID
                            "dimension": "ROWS",
                            "startIndex": row_index - 1,  # Convert to 0-based index
                            "endIndex": row_index,  # Exclusive end index
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
        return json.dumps(
            {
                "status": "success",
                "message": f"Rows {row_indices} deleted successfully.",
            }
        )
    except Exception as e:
        logger.error(f"Failed to delete rows from sheet: {str(e)}")
        return json.dumps(
            {"status": "error", "error": f"Failed to delete rows from sheet: {str(e)}"}
        )  # JSON-compatible error response
