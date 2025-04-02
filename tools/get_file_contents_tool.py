import json
import io
from typing import Optional
from typing_extensions import Annotated
from pydantic import Field
from PyPDF2 import PdfReader
from core.utils.logger import logger  # Importing the logger
from core.utils.state import global_state  # Import global state
from app.middleware.google.GoogleAuthMiddleware import check_access


def get_file_contents_tool(
    document_id: Annotated[
        str, Field(description="The ID of the document to retrieve contents from.")
    ],
) -> str:
    """
    Retrieves the contents of a document based on its type (Google Docs, Google Sheets, PDF, or text).

    Args:
    - document_id (str): The ID of the document to retrieve.

    Returns:
    - JSON string indicating success or error, along with the document contents.
    """

    # Retrieve the Google Drive service from global state
    service = global_state.get("google_drive_service")
    if service is None:
        logger.error("Google Drive service is not available in global state.")
        return json.dumps(
            {"status": "error", "error": "Google Drive service is not initialized."}
        )

    try:
        # Get the document metadata to check its MIME type
        file_metadata = (
            service.files().get(fileId=document_id, fields="mimeType").execute()
        )
        mime_type = file_metadata.get("mimeType")

        logger.info(f"Document ID: {document_id}, MIME type: {mime_type}")

        # Determine the type of file and call the appropriate function
        if mime_type == "application/vnd.google-apps.document":
            return get_google_doc_contents(document_id)
        elif mime_type == "application/vnd.google-apps.spreadsheet":
            return get_google_sheet_contents(document_id)
        elif mime_type == "application/pdf":
            return download_pdf_and_extract_text(document_id)
        elif mime_type == "text/plain":
            return download_text_file(document_id)
        else:
            return json.dumps({"status": "error", "error": "Unsupported file type."})

    except Exception as e:
        logger.error(f"Failed to retrieve document contents: {str(e)}")
        return json.dumps(
            {
                "status": "error",
                "error": f"Failed to retrieve document contents: {str(e)}",
            }
        )


def get_google_doc_contents(document_id: str) -> str:
    """
    Retrieves the contents of a Google Docs document.

    Args:
    - document_id (str): The ID of the document to retrieve.

    Returns:
    - JSON string indicating success or error, along with the document contents.
    """
    service = global_state.get("google_docs_service")
    if service is None:
        logger.error("Google Docs service is not available in global state.")
        return json.dumps(
            {"status": "error", "error": "Google Docs service is not initialized."}
        )

    try:
        logger.info(f"Attempting to retrieve document with ID: {document_id}")
        doc = service.documents().get(documentId=document_id).execute()
        content = []

        for element in doc.get("body", {}).get("content", []):
            if "paragraph" in element:
                for text_run in element["paragraph"].get("elements", []):
                    if "textRun" in text_run:
                        content.append(text_run["textRun"]["content"])

        document_content = "".join(content)

        logger.info(f"Successfully retrieved contents for document ID: {document_id}.")
        return json.dumps(
            {
                "status": "success",
                "content": document_content,
            }
        )
    except Exception as e:
        logger.error(f"Failed to retrieve document contents: {str(e)}")
        return json.dumps(
            {
                "status": "error",
                "error": f"Failed to retrieve document contents: {str(e)}",
            }
        )


def get_google_sheet_contents(sheet_id: str) -> str:
    """
    Retrieves the contents of a Google Sheets document.

    Args:
    - sheet_id (str): The ID of the Google Sheets document to retrieve.

    Returns:
    - JSON string indicating success or error, along with the sheet contents.
    """

    # Check authentication
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    service = global_state.get("google_sheets_service")
    if service is None:
        logger.error("Google Sheets service is not available in global state.")
        return json.dumps(
            {"status": "error", "error": "Google Sheets service is not initialized."}
        )

    try:
        logger.info(f"Attempting to retrieve sheet with ID: {sheet_id}")

        # Retrieve the spreadsheet metadata
        sheet_metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        data = sheet_metadata.get("sheets", [])

        if not data:
            logger.warning(f"No sheets found in the spreadsheet with ID: {sheet_id}.")
            return json.dumps(
                {"status": "error", "error": "No sheets found in the spreadsheet."}
            )

        # Get the first sheet's title
        first_sheet = data[0]
        title = first_sheet.get("properties", {}).get("title", "Sheet")

        # Now retrieve the actual values from the sheet
        values_response = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=sheet_id, range=title)
            .execute()
        )
        values = values_response.get("values", [])

        if not values:
            logger.warning(f"No data found in sheet titled '{title}'.")
            return json.dumps(
                {
                    "status": "error",
                    "error": f"No data found in sheet titled '{title}'.",
                }
            )

        sheet_content = {
            "title": title,
            "values": values,
        }

        logger.info(f"Successfully retrieved contents for sheet ID: {sheet_id}.")
        return json.dumps(
            {
                "status": "success",
                "content": sheet_content,
            }
        )
    except Exception as e:
        logger.error(f"Failed to retrieve sheet contents: {str(e)}")
        return json.dumps(
            {"status": "error", "error": f"Failed to retrieve sheet contents: {str(e)}"}
        )


def download_pdf_and_extract_text(file_id: str) -> str:
    """
    Downloads a PDF file from Google Drive and extracts its text content.

    Args:
    - file_id (str): The ID of the PDF file to download.

    Returns:
    - JSON string indicating success or error, along with the extracted text content.
    """
    service = global_state.get("google_drive_service")
    if service is None:
        logger.error("Google Drive service is not available in global state.")
        return json.dumps(
            {"status": "error", "error": "Google Drive service is not initialized."}
        )

    try:
        request = service.files().get_media(fileId=file_id)
        file_handle = io.BytesIO(request.execute())

        pdf_reader = PdfReader(file_handle)
        text_content = []

        for page in pdf_reader.pages:
            text_content.append(page.extract_text())

        document_content = "\n".join(text_content)

        logger.info(f"Successfully retrieved contents for PDF file ID: {file_id}.")
        return json.dumps(
            {
                "status": "success",
                "content": document_content,
            }
        )
    except Exception as e:
        logger.error(f"Failed to retrieve PDF contents: {str(e)}")
        return json.dumps(
            {"status": "error", "error": f"Failed to retrieve PDF contents: {str(e)}"}
        )


def download_text_file(file_id: str) -> str:
    """
    Downloads a text file from Google Drive and retrieves its content.

    Args:
    - file_id (str): The ID of the text file to download.

    Returns:
    - JSON string indicating success or error, along with the text content.
    """
    service = global_state.get("google_drive_service")
    if service is None:
        logger.error("Google Drive service is not available in global state.")
        return json.dumps(
            {"status": "error", "error": "Google Drive service is not initialized."}
        )

    try:
        request = service.files().get_media(fileId=file_id)
        file_handle = io.BytesIO(request.execute())
        text_content = file_handle.getvalue().decode("utf-8")

        logger.info(f"Successfully retrieved contents for text file ID: {file_id}.")
        return json.dumps(
            {
                "status": "success",
                "content": text_content,
            }
        )
    except Exception as e:
        logger.error(f"Failed to retrieve text file contents: {str(e)}")
        return json.dumps(
            {
                "status": "error",
                "error": f"Failed to retrieve text file contents: {str(e)}",
            }
        )
