from typing import Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger
from core.utils.state import global_state
from core.utils.env import EnvConfig
from app.middleware.google.GoogleAuthMiddleware import check_access
from core.utils.tools import doc_tag
from googleapiclient.http import MediaFileUpload  # Import MediaFileUpload
import json
import csv
import os


@doc_tag("Drive")
def create_file_tool(
    title: Annotated[
        str, Field(description="The title or name of the file to create.")
    ],
    content: Annotated[str, Field(description="The content to be added to the file.")],
    file_type: Annotated[
        str, Field(description="The type of the file to create (text, json, or csv).")
    ],
    parent_folder_id: Annotated[
        Optional[str],
        Field(
            description="The ID of the parent folder to create the file in (optional)."
        ),
    ] = None,
) -> dict:
    """
    Creates a new text, JSON, or CSV file with the specified content and uploads it to Google Drive.

    Args:
    - title (str): The title of the file to create.
    - content (str): The content to be added to the file.
    - file_type (str): The type of the file to create ("text", "json", or "csv").
    - parent_folder_id (str, optional): The ID of the parent folder to create the file in.

    Returns:
    - A dictionary indicating success or error, without JSON serialization.
    """

    # Check authentication for Google Drive
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Ensure Google Drive service is available
    drive_service = global_state.get("google_drive_service")
    if drive_service is None:
        logger.error("Google Drive service is not available in global state.")
        return {
            "status": "error",
            "error": f"Google Drive permission scope not available, please add this scope here: {EnvConfig.get('APP_HOST')}/auth/login",
        }

    try:
        # Prepare content based on file type
        file_content = ""
        mime_type = ""

        if file_type == "text":
            file_content = content
            mime_type = "text/plain"

        elif file_type == "json":
            # Try to parse the content as JSON
            try:
                json_content = json.loads(content)
                file_content = json.dumps(json_content, indent=4)
            except json.JSONDecodeError:
                return {"status": "error", "error": "Invalid JSON content."}
            mime_type = "application/json"

        elif file_type == "csv":
            # Prepare content for CSV (assuming content is comma-separated for simplicity)
            lines = content.splitlines()
            try:
                csv_content = [line.split(",") for line in lines]
                file_content = "\n".join([",".join(line) for line in csv_content])
            except Exception as e:
                return {"status": "error", "error": f"Invalid CSV content: {str(e)}"}
            mime_type = "text/csv"

        else:
            return {
                "status": "error",
                "error": "Unsupported file type. Please use 'text', 'json', or 'csv'.",
            }

        # Save content to a temporary file
        temp_file_path = f"/tmp/{title}"
        with open(temp_file_path, "w") as f:
            f.write(file_content)

        file_metadata = {"name": title, "mimeType": mime_type}

        # Handle file upload
        media = MediaFileUpload(temp_file_path, mimetype=mime_type)

        file = (
            drive_service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        file_id = file.get("id")

        # If a parent folder ID is provided, move the file to that folder
        if parent_folder_id:
            drive_service.files().update(
                fileId=file_id,
                addParents=parent_folder_id,
                removeParents="",
                fields="id, parents",
            ).execute()

        # Clean up the temporary file
        os.remove(temp_file_path)

        logger.info(
            f"Successfully created and uploaded '{file_metadata['name']}' with ID: {file_id}."
        )
        return {
            "status": "success",
            "message": "File created and uploaded successfully.",
            "file_id": file_id,
        }

    except Exception as e:
        logger.error(f"Failed to create file: {str(e)}")
        return {"status": "error", "error": f"Failed to create file: {str(e)}"}
