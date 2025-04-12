from typing import Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger
from core.utils.state import global_state
from core.utils.env import EnvConfig
from app.middleware.google.GoogleAuthMiddleware import check_access
from core.utils.tools import doc_tag


@doc_tag("Docs")
def create_document_tool(
    title: Annotated[
        str, Field(description="The title of the document to create. Ex: 'My Document'")
    ],
    content: Annotated[
        str, Field(description="The content to be added to the document.")
    ],
    parent_folder_id: Annotated[
        Optional[str],
        Field(
            description="The ID of the parent folder to create the document in (optional)."
        ),
    ] = None,
) -> dict:
    """
    Creates a new Google Docs document with the specified content.

    Args:
    - title (str): The title of the document to create.
    - content (str): The content to be added to the document.
    - parent_folder_id (str, optional): The ID of the parent folder to create the document in.

    Returns:
    - A dictionary indicating success or error, without JSON serialization.
    """

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    service = global_state.get("google_docs_service")
    if service is None:
        logger.error("Google Docs service is not available in global state.")
        return {
            "status": "error",
            "error": f"Google Docs permission scope not available, please add this scope here: {EnvConfig.get('APP_HOST')}/auth/login",
        }

    try:
        # Create the document
        doc_metadata = {"title": title}
        doc = service.documents().create(body=doc_metadata).execute()
        document_id = doc.get("documentId")

        # Insert content into the document
        requests = [
            {
                "insertText": {
                    "location": {
                        "index": 1,
                    },
                    "text": content,
                }
            }
        ]
        service.documents().batchUpdate(
            documentId=document_id, body={"requests": requests}
        ).execute()

        # If a parent folder ID is provided, move the document to that folder
        if parent_folder_id:
            drive_service = global_state.get(
                "google_drive_service"
            )  # Get the Google Drive service
            if drive_service is None:
                logger.error("Google Drive service is not available in global state.")
                return {
                    "status": "error",
                    "error": "Google Drive service is not initialized.",
                }

            # Move the document to the specified folder
            drive_service.files().update(
                fileId=document_id,
                addParents=parent_folder_id,
                removeParents="",
                fields="id, parents",
            ).execute()

        logger.info(f"Successfully created document '{title}' with ID: {document_id}.")
        return {
            "status": "success",
            "message": "Document created successfully.",
            "document_id": document_id,
        }
    except Exception as e:
        logger.error(f"Failed to create document: {str(e)}")
        return {"status": "error", "error": f"Failed to create document: {str(e)}"}
