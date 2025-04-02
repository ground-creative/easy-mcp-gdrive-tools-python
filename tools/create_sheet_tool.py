import json
from typing import Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state  # Import global state
from app.middleware.google.GoogleAuthMiddleware import check_access


def create_google_sheet_tool(
    title: Annotated[
        str, Field(description="The title of the sheet to create. Ex: 'My Spreadsheet'")
    ],
    parent_folder_id: Annotated[
        Optional[str],
        Field(
            description="The ID of the parent folder to create the sheet in (optional)."
        ),
    ] = None,
) -> str:  # Change return type to str
    """
    Creates a new Google Sheets document with the specified title.

    Args:
    - title (str): The title of the sheet to create.
    - parent_folder_id (str, optional): The ID of the parent folder to create the sheet in.

    Returns:
    - JSON string indicating success or error.

    Example Response on Success:
    {
        "status": "success",
        "message": "Sheet created successfully.",
        "sheet_id": "abcdef1234567890"
    }
    """

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve the Google Sheets service from global state
    service = global_state.get(
        "google_sheets_service"
    )  # Ensure you are using the correct service
    if service is None:
        logger.error("Google Sheets service is not available in global state.")
        return json.dumps(
            {"status": "error", "error": "Google Sheets service is not initialized."}
        )

    try:
        # Create the sheet
        sheet_metadata = {"properties": {"title": title}}
        sheet = service.spreadsheets().create(body=sheet_metadata).execute()
        sheet_id = sheet.get("spreadsheetId")

        # If a parent folder ID is provided, move the sheet to that folder
        if parent_folder_id:
            drive_service = global_state.get(
                "google_drive_service"
            )  # Get the Google Drive service
            if drive_service is None:
                logger.error("Google Drive service is not available in global state.")
                return json.dumps(
                    {
                        "status": "error",
                        "error": "Google Drive service is not initialized.",
                    }
                )

            # Attempt to move the sheet to the specified folder
            try:
                drive_service.files().update(
                    fileId=sheet_id,
                    addParents=parent_folder_id,
                    removeParents="",
                    fields="id, parents",
                ).execute()
                logger.info(
                    f"Successfully moved sheet '{title}' to folder ID: {parent_folder_id}."
                )
            except Exception as e:
                logger.error(f"Failed to move sheet to folder: {str(e)}")
                return json.dumps(
                    {
                        "status": "error",
                        "error": f"Failed to move sheet to folder: {str(e)}",
                    }
                )

        logger.info(f"Successfully created sheet '{title}' with ID: {sheet_id}.")
        return json.dumps(
            {
                "status": "success",
                "message": "Sheet created successfully.",
                "sheet_id": sheet_id,
            }
        )
    except Exception as e:
        logger.error(f"Failed to create sheet: {str(e)}")
        return json.dumps(
            {"status": "error", "error": f"Failed to create sheet: {str(e)}"}
        )  # JSON-compatible error response
