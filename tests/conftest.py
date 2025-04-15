import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from app.middleware.google.database import init_db
from core.utils.state import global_state
from core.utils.logger import logger
from core.utils.env import EnvConfig
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from app.utils.credentials import attach_google_services
from app.tools.create_folder import gdrive_create_folder_tool
from app.tools.delete_item import gdrive_delete_item_tool
from app.tools.create_document import gdrive_create_document_tool
from app.tools.create_sheet import gdrive_create_sheet_tool


@pytest.fixture(scope="module")
def auth_setup():
    root_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    init_db("test", f"{root_folder}/storage/sqlite_credentials.db")
    global_state.set("middleware.GoogleAuthMiddleware.is_authenticated", False, True)
    db_handler = global_state.get("db_handler")
    cred = db_handler.get_credentials(EnvConfig.get("TEST_TOKEN"))

    credentials = cred["credentials"]
    try:
        creds = Credentials.from_authorized_user_info(credentials)
    except Exception as e:
        logger.error(f"Error initializing credentials: {str(e)}")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("GoogleAuthMiddleware: Refreshing expired credentials.")
            try:
                creds = Credentials(
                    None,
                    refresh_token=creds.refresh_token,
                    client_id=creds.client_id,
                    client_secret=creds.client_secret,
                    token_uri="https://oauth2.googleapis.com/token",
                )
                creds.refresh(GoogleRequest())
                id_info = id_token.verify_oauth2_token(
                    creds.id_token,
                    google_requests.Request(),
                    creds.client_id,
                )
                user_id = id_info["sub"]
                logger.info(
                    f"GoogleAuthMiddleware new access token for user {user_id}: {creds.token}"
                )
                db_handler.update_access_token(user_id, creds.token)

            except Exception as e:
                logger.error(
                    f"GoogleAuthMiddleware error refreshing credentials: {str(e)}",
                    exc_info=True,
                )
                global_state.set(
                    "middleware.GoogleAuthMiddleware.error_message",
                    f"There has been an error with authenticating, please go to {EnvConfig.get('APP_HOST')}/auth/login and authenticate again",
                    True,
                )
                return
        else:
            logger.warning("GoogleAuthMiddleware: Invalid credentials.")
            global_state.set(
                "middleware.GoogleAuthMiddleware.error_message",
                f"There has been an error with authenticating, please deauthenticate the app and go to {EnvConfig.get('APP_HOST')}/auth/login",
                True,
            )
            return

    global_state.set("middleware.GoogleAuthMiddleware.is_authenticated", True, True)
    attach_google_services(creds)


@pytest.fixture(scope="module")
def create_folder_setup():
    test_folder_name = "Test MCP Gdrive Folder"
    global_state.set("test_folder_name", test_folder_name, True)

    # Create folder
    response = gdrive_create_folder_tool(folder_name=test_folder_name)
    assert response["status"] == "success", "Failed to create folder"
    folder_id = response["data"]["id"]
    global_state.set("test_folder_id", folder_id, True)

    # Yield so the test can run, then clean up
    yield folder_id

    # Teardown - delete the created folder with confirmation token
    # First, attempt to delete the folder without the confirmation token to get one
    delete_response = gdrive_delete_item_tool(file_id=folder_id)

    # Assert that the confirmation token is returned
    assert (
        "confirmation_token" in delete_response
    ), "No confirmation token received for deletion"

    confirmation_token = delete_response["confirmation_token"]

    # Now confirm the deletion using the received confirmation token
    final_delete_response = gdrive_delete_item_tool(
        file_id=folder_id, confirmation_token=confirmation_token
    )

    # Assert the deletion was successful
    assert (
        final_delete_response["status"] == "success"
    ), "Failed to delete folder after confirmation"


@pytest.fixture(scope="module")
def create_doc_setup():
    test_doc_title = "Test MCP Gdrive Doc"
    global_state.set("test_doc_title", test_doc_title, True)
    subfolder_id = global_state.get("test_folder_id")

    # Create document
    response = gdrive_create_document_tool(
        title=test_doc_title,
        content="testing mcp server",
        parent_folder_id=subfolder_id,
    )
    assert response["status"] == "success", "Failed to create document"
    document_id = response["document_id"]
    global_state.set("test_doc_id", document_id, True)

    # Yield so the test can run, then clean up
    yield document_id

    delete_response = gdrive_delete_item_tool(file_id=document_id)

    # Assert that the confirmation token is returned
    assert (
        "confirmation_token" in delete_response
    ), "No confirmation token received for deletion"

    confirmation_token = delete_response["confirmation_token"]

    # Now confirm the deletion using the received confirmation token
    final_delete_response = gdrive_delete_item_tool(
        file_id=document_id, confirmation_token=confirmation_token
    )

    # Assert the deletion was successful
    assert (
        final_delete_response["status"] == "success"
    ), "Failed to delete folder after confirmation"


@pytest.fixture(scope="module")
def create_sheet_setup():
    test_sheet_title = "Test MCP Gdrive Sheet"
    global_state.set("test_sheet_title", test_sheet_title, True)
    subfolder_id = global_state.get("test_folder_id")

    # Create sheet
    response = gdrive_create_sheet_tool(
        title=test_sheet_title,
        parent_folder_id=subfolder_id,
    )
    assert response["status"] == "success", "Failed to create sheet"
    document_id = response["sheet_id"]
    global_state.set("test_sheet_id", document_id, True)

    # Yield so the test can run, then clean up
    yield document_id

    delete_response = gdrive_delete_item_tool(file_id=document_id)

    # Assert that the confirmation token is returned
    assert (
        "confirmation_token" in delete_response
    ), "No confirmation token received for deletion"

    confirmation_token = delete_response["confirmation_token"]

    # Now confirm the deletion using the received confirmation token
    final_delete_response = gdrive_delete_item_tool(
        file_id=document_id, confirmation_token=confirmation_token
    )

    # Assert the deletion was successful
    assert (
        final_delete_response["status"] == "success"
    ), "Failed to delete folder after confirmation"