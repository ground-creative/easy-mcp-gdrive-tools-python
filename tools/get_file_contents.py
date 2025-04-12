import io
from typing_extensions import Annotated
from pydantic import Field
from PyPDF2 import PdfReader
from core.utils.logger import logger
from core.utils.state import global_state
from core.utils.env import EnvConfig
from app.middleware.google.GoogleAuthMiddleware import check_access
from core.utils.tools import doc_tag
import csv
import json


@doc_tag("Drive")
def get_file_contents_tool(
    file_id: Annotated[
        str, Field(description="The ID of the file to retrieve contents from.")
    ],
) -> dict:
    """
    Retrieves the contents of a file based on its type (Google Docs, Google Sheets, PDF, text, JSON or CSV).

    Args:
    - file_id (str): The ID of the file to retrieve.

    Returns:
    - JSON string indicating success or error, along with the file contents.
    """
    service = global_state.get("google_drive_service")
    if service is None:
        logger.error("Google Drive service is not available in global state.")
        return {
            "status": "error",
            "error": f"Google Drive permission scope not available, please add this scope here: {EnvConfig.get('APP_HOST')}/auth/login",
        }

    try:
        file_metadata = service.files().get(fileId=file_id, fields="mimeType").execute()
        mime_type = file_metadata.get("mimeType")

        logger.info(f"File ID: {file_id}, MIME type: {mime_type}")

        if mime_type == "application/vnd.google-apps.document":
            return get_google_doc_contents(file_id)
        elif mime_type == "application/vnd.google-apps.spreadsheet":
            return get_google_sheet_contents(file_id)
        elif mime_type == "application/pdf":
            return download_pdf_and_extract_text(file_id)
        elif mime_type == "text/plain":
            return download_text_file(file_id)
        elif mime_type == "text/csv":
            return download_csv_file(file_id)
        elif mime_type == "application/json":
            return download_json_file(file_id)
        else:
            return {"status": "error", "error": "Unsupported file type."}

    except Exception as e:
        logger.error(f"Failed to retrieve file contents: {str(e)}")
        return {"status": "error", "error": str(e)}


def get_google_doc_contents(file_id: str) -> dict:
    service = global_state.get("google_docs_service")
    if service is None:
        logger.error("Google Docs service is not available in global state.")
        return {"status": "error", "error": "Google Docs service is not initialized."}

    try:
        logger.info(f"Attempting to retrieve document with ID: {file_id}")
        doc = service.documents().get(documentId=file_id).execute()
        content = []

        for element in doc.get("body", {}).get("content", []):
            if "paragraph" in element:
                for text_run in element["paragraph"].get("elements", []):
                    if "textRun" in text_run:
                        content.append(text_run["textRun"]["content"])

        file_content = "".join(content)

        if not file_content.strip():  # Check if content is empty
            logger.info(f"File ID: {file_id} is empty.")
            return {"status": "success", "content": ""}

        logger.info(f"Successfully retrieved contents for file ID: {file_id}.")
        return {"status": "success", "content": file_content}
    except Exception as e:
        logger.error(f"Failed to retrieve document contents: {str(e)}")
        return {"status": "error", "error": str(e)}


def get_google_sheet_contents(file_id: str) -> dict:
    auth_response = check_access(True)
    if auth_response:
        return auth_response

    service = global_state.get("google_sheets_service")
    if service is None:
        logger.error("Google Sheets service is not available in global state.")
        return {"status": "error", "error": "Google Sheets service is not initialized."}

    try:
        logger.info(f"Attempting to retrieve sheet with ID: {file_id}")
        sheet_metadata = service.spreadsheets().get(spreadsheetId=file_id).execute()
        data = sheet_metadata.get("sheets", [])

        if not data:
            return {"status": "error", "error": "No sheets found in the spreadsheet."}

        title = data[0].get("properties", {}).get("title", "Sheet")
        values_response = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=file_id, range=title)
            .execute()
        )
        values = values_response.get("values", [])

        if not values:
            return {"status": "success", "content": {"title": title, "values": []}}

        logger.info(f"Successfully retrieved contents for sheet ID: {file_id}.")
        return {"status": "success", "content": {"title": title, "values": values}}

    except Exception as e:
        logger.error(f"Failed to retrieve sheet contents: {str(e)}")
        return {"status": "error", "error": str(e)}


def download_pdf_and_extract_text(file_id: str) -> dict:
    service = global_state.get("google_drive_service")
    if service is None:
        logger.error("Google Drive service is not available in global state.")
        return {"status": "error", "error": "Google Drive service is not initialized."}

    try:
        request = service.files().get_media(fileId=file_id)
        file_handle = io.BytesIO(request.execute())

        pdf_reader = PdfReader(file_handle)
        text_content = [page.extract_text() for page in pdf_reader.pages]

        # Check if extracted text is empty
        if not any(text_content):
            logger.info(f"File ID: {file_id} is empty.")
            return {"status": "success", "content": ""}

        logger.info(f"Successfully retrieved contents for PDF file ID: {file_id}.")
        return {"status": "success", "content": "\n".join(text_content)}

    except Exception as e:
        logger.error(f"Failed to retrieve PDF contents: {str(e)}")
        return {"status": "error", "error": str(e)}


def download_text_file(file_id: str) -> dict:
    service = global_state.get("google_drive_service")
    if service is None:
        logger.error("Google Drive service is not available in global state.")
        return {"status": "error", "error": "Google Drive service is not initialized."}

    try:
        request = service.files().get_media(fileId=file_id)
        file_handle = io.BytesIO(request.execute())
        text_content = file_handle.getvalue().decode("utf-8")

        # Check if the text content is empty
        if not text_content.strip():
            logger.info(f"File ID: {file_id} is empty.")
            return {"status": "success", "content": ""}

        logger.info(f"Successfully retrieved contents for text file ID: {file_id}.")
        return {"status": "success", "content": text_content}

    except Exception as e:
        logger.error(f"Failed to retrieve text file contents: {str(e)}")
        return {"status": "error", "error": str(e)}


def download_json_file(file_id: str) -> dict:
    service = global_state.get("google_drive_service")
    if service is None:
        logger.error("Google Drive service is not available in global state.")
        return {"status": "error", "error": "Google Drive service is not initialized."}

    try:
        request = service.files().get_media(fileId=file_id)
        file_handle = io.BytesIO(request.execute())
        json_content = json.loads(file_handle.getvalue().decode("utf-8"))

        logger.info(f"Successfully retrieved contents for JSON file ID: {file_id}.")
        return {"status": "success", "content": json_content}

    except Exception as e:
        logger.error(f"Failed to retrieve JSON file contents: {str(e)}")
        return {"status": "error", "error": str(e)}


def download_csv_file(file_id: str) -> dict:
    service = global_state.get("google_drive_service")
    if service is None:
        logger.error("Google Drive service is not available in global state.")
        return {"status": "error", "error": "Google Drive service is not initialized."}

    try:
        request = service.files().get_media(fileId=file_id)
        file_handle = io.StringIO(request.execute().decode("utf-8"))
        reader = csv.reader(file_handle)
        values = list(reader)

        if not values:
            logger.info(f"File ID: {file_id} is empty.")
            return {"status": "success", "content": []}

        logger.info(f"Successfully retrieved contents for CSV file ID: {file_id}.")
        return {"status": "success", "content": values}

    except Exception as e:
        logger.error(f"Failed to retrieve CSV file contents: {str(e)}")
        return {"status": "error", "error": str(e)}
