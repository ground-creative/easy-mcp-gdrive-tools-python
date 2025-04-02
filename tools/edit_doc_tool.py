import json
from typing import Dict
from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state  # Import global state
from app.middleware.google.GoogleAuthMiddleware import check_access


def edit_google_doc_tool(
    document_id: Annotated[
        str,
        Field(
            description="The ID of the Google Docs document to edit. Ex: 'abcdef1234567890'"
        ),
    ],
    new_content: Annotated[
        str, Field(description="The new content to replace in the document.")
    ],
) -> str:  # Change return type to str
    """
    Edits an existing Google Docs document with the specified content.

    Args:
    - document_id (str): The ID of the Google Docs document to edit.
    - new_content (str): The new content to be added to the document.

    Returns:
    - JSON string indicating success or error.

    Example Response on Success:
    {
        "status": "success",
        "message": "Document edited successfully."
    }
    """

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    # Retrieve the Google Docs service from global state
    service = global_state.get("google_docs_service")
    if service is None:
        logger.error("Google Docs service is not available in global state.")
        return json.dumps(
            {"status": "error", "error": "Google Docs service is not initialized."}
        )

    try:
        # Retrieve the document to get its current content length
        doc = service.documents().get(documentId=document_id).execute()
        content_length = len(doc.get("body").get("content"))

        # Prepare the request to clear existing content
        clear_requests = [
            {
                "deleteContentRange": {
                    "range": {
                        "startIndex": 1,  # Start after the document title
                        "endIndex": content_length - 1,  # Use the actual content length
                    }
                }
            }
        ]

        # Call the Docs API to clear the document content
        service.documents().batchUpdate(
            documentId=document_id, body={"requests": clear_requests}
        ).execute()

        # Prepare the request to insert new content
        insert_requests = [
            {
                "insertText": {
                    "location": {"index": 1},  # Insert at the start of the document
                    "text": new_content,
                }
            }
        ]

        # Call the Docs API to insert the new content
        service.documents().batchUpdate(
            documentId=document_id, body={"requests": insert_requests}
        ).execute()

        logger.info(f"Successfully edited document with ID: {document_id}.")
        return json.dumps(
            {"status": "success", "message": "Document edited successfully."}
        )
    except Exception as e:
        logger.error(f"Failed to edit document: {str(e)}")
        return json.dumps(
            {"status": "error", "error": f"Failed to edit document: {str(e)}"}
        )  # JSON-compatible error response
