from typing import Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger
from core.utils.state import global_state
from core.utils.env import EnvConfig
from app.middleware.google.GoogleAuthMiddleware import check_access
from core.utils.tools import doc_tag, doc_name


@doc_tag("Spreadsheets")
@doc_name("Create spreadsheet")
def gdrive_create_sheet_tool(
    title: Annotated[
        str, Field(description="The title of the sheet to create. Ex: 'My Spreadsheet'")
    ],
    parent_folder_id: Annotated[
        Optional[str],
        Field(
            description="The ID of the parent folder to create the sheet in (optional)."
        ),
    ] = None,
) -> dict:
    """
    Creates a new Google Sheets document with the specified title.

    * Requires permission scope for spreadsheets.

    Args:
    - title (str): The title of the sheet to create.
    - parent_folder_id (str, optional): The ID of the parent folder to create the sheet in.

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
        # Create the sheet
        sheet_metadata = {"properties": {"title": title}}
        sheet = service.spreadsheets().create(body=sheet_metadata).execute()
        sheet_id = sheet.get("spreadsheetId")

        # If a parent folder ID is provided, move the sheet to that folder
        if parent_folder_id:
            drive_service = global_state.get("google_drive_service")
            if drive_service is None:
                logger.error("Google Drive service is not available in global state.")
                return {
                    "status": "error",
                    "error": "Google Drive service is not initialized.",
                }

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
                return {
                    "status": "error",
                    "error": f"{str(e)}",
                }

        logger.info(f"Successfully created sheet '{title}' with ID: {sheet_id}.")
        return {
            "status": "success",
            "message": "Sheet created successfully.",
            "sheet_id": sheet_id,
        }

    except Exception as e:
        logger.error(f"Failed to create sheet: {str(e)}")
        return {
            "status": "error",
            "error": f"{str(e)}",
        }
