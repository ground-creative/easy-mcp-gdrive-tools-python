from typing_extensions import Annotated
from pydantic import Field
from core.utils.logger import logger
from core.utils.state import global_state
from core.utils.env import EnvConfig
from app.middleware.google.GoogleAuthMiddleware import check_access
from googleapiclient.errors import HttpError
from core.utils.tools import doc_tag, doc_name


@doc_tag("Documents")
@doc_name("Edit document")
def gdrive_edit_document_tool(
    document_id: Annotated[
        str,
        Field(
            description="The ID of the Google Docs document to edit. Ex: 'abcdef1234567890'"
        ),
    ],
    new_content: Annotated[
        str,
        Field(description="The new content to replace in the document."),
    ],
) -> dict:
    """
    Edits an existing Google Docs document with the specified content.

    * Requires permission scope for documents

    Args:
    - document_id (str): The ID of the Google Docs document to edit.
    - new_content (str): The new content to be added to the document.

    Returns:
    - A dictionary indicating success or error.
    """
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
        # Fetch document content
        doc = service.documents().get(documentId=document_id).execute()

        # Insert new content at the start of the document
        insert_requests = [
            {
                "insertText": {
                    "location": {
                        "index": 1  # Insert at the very start of the document
                    },
                    "text": new_content,
                }
            }
        ]

        service.documents().batchUpdate(
            documentId=document_id, body={"requests": insert_requests}
        ).execute()

        logger.info(f"Successfully edited document with ID: {document_id}.")
        return {"status": "success", "message": "Document edited successfully."}

    except HttpError as e:
        error_msg = None

        try:
            if hasattr(e, "error_details") and isinstance(e.error_details, list):
                first_error = e.error_details[0]
                if isinstance(first_error, dict):
                    error_msg = first_error.get("message")
        except Exception as parse_error:
            logger.warning(f"Failed to parse HttpError details: {parse_error}")

        if not error_msg:
            error_msg = str(e)

        logger.error(f"Google API error: {error_msg}")
        return {"status": "error", "error": f"Google API error: {error_msg}"}

    except Exception as e:
        logger.error(f"Failed to edit document: {str(e)}")
        return {"status": "error", "error": f"Failed to edit document: {str(e)}"}
