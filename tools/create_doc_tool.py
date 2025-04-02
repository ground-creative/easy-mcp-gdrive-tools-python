import json
from typing import Dict, Optional
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state  # Import global state
from app.middleware.google.GoogleAuthMiddleware import check_access


def create_google_doc_tool(
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
    ] = None,  # Optional parameter for parent folder ID
) -> str:  # Change return type to str
    """
    Creates a new Google Docs document with the specified content.

    Args:
    - title (str): The title of the document to create.
    - content (str): The content to be added to the document.
    - parent_folder_id (str, optional): The ID of the parent folder to create the document in.

    Returns:
    - JSON string indicating success or error.

    Example Response on Success:
    {
        "status": "success",
        "message": "Document created successfully.",
        "document_id": "abcdef1234567890"
    }
    """

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve the Google Docs service from global state
    service = global_state.get(
        "google_docs_service"
    )  # Ensure you are using the correct service
    if service is None:
        logger.error("Google Docs service is not available in global state.")
        return json.dumps(
            {"status": "error", "error": "Google Docs service is not initialized."}
        )

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
                return json.dumps(
                    {
                        "status": "error",
                        "error": "Google Drive service is not initialized.",
                    }
                )

            # Move the document to the specified folder
            drive_service.files().update(
                fileId=document_id,
                addParents=parent_folder_id,
                removeParents="",
                fields="id, parents",
            ).execute()

        logger.info(f"Successfully created document '{title}' with ID: {document_id}.")
        return json.dumps(
            {
                "status": "success",
                "message": "Document created successfully.",
                "document_id": document_id,
            }
        )
    except Exception as e:
        logger.error(f"Failed to create document: {str(e)}")
        return json.dumps(
            {"status": "error", "error": f"Failed to create document: {str(e)}"}
        )  # JSON-compatible error response
