import os
import sys
from core.utils.state import global_state
from app.tools.create_document import create_document_tool
from app.tools.delete_item import delete_item_tool
from app.tools.get_file_contents import get_file_contents_tool
from app.tools.edit_document import edit_document_tool


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def test_create_and_delete(auth_setup):

    is_authenticated = global_state.get(
        "middleware.GoogleAuthMiddleware.is_authenticated"
    )
    assert is_authenticated, "Not authenticated"

    response = create_document_tool(
        title="test_create_and_delete_doc", content="testing mcp server"
    )
    assert response["status"] == "success", "Failed to create folder"
    document_id = response["document_id"]

    delete_response = delete_item_tool(file_id=document_id)

    # Assert that the confirmation token is returned
    assert (
        "confirmation_token" in delete_response
    ), "No confirmation token received for deletion"

    confirmation_token = delete_response["confirmation_token"]

    # Now confirm the deletion using the received confirmation token
    final_delete_response = delete_item_tool(
        file_id=document_id, confirmation_token=confirmation_token
    )

    # Assert the deletion was successful
    assert (
        final_delete_response["status"] == "success"
    ), "Failed to delete folder after confirmation"


def test_create_and_delete_in_subfolder(auth_setup, create_folder_setup):
    subfolder_id = global_state.get("test_folder_id")
    is_authenticated = global_state.get(
        "middleware.GoogleAuthMiddleware.is_authenticated"
    )
    assert is_authenticated, "Not authenticated"

    response = create_document_tool(
        title="test_create_and_delete_doc",
        content="testing mcp server",
        parent_folder_id=subfolder_id,
    )
    assert response["status"] == "success", "Failed to create folder"
    document_id = response["document_id"]

    delete_response = delete_item_tool(file_id=document_id)

    # Assert that the confirmation token is returned
    assert (
        "confirmation_token" in delete_response
    ), "No confirmation token received for deletion"

    confirmation_token = delete_response["confirmation_token"]

    # Now confirm the deletion using the received confirmation token
    final_delete_response = delete_item_tool(
        file_id=document_id, confirmation_token=confirmation_token
    )

    # Assert the deletion was successful
    assert (
        final_delete_response["status"] == "success"
    ), "Failed to delete folder after confirmation"


def test_get_contents_tool(auth_setup, create_folder_setup, create_doc_setup):
    test_doc_id = global_state.get("test_doc_id")
    is_authenticated = global_state.get(
        "middleware.GoogleAuthMiddleware.is_authenticated"
    )
    assert is_authenticated, "Not authenticated"

    response = get_file_contents_tool(file_id=test_doc_id)

    # Check that the response is successful and contains content
    assert (
        response["status"] == "success"
    ), f"Failed to fetch file: {response.get('error')}"
    assert (
        "content" in response and response["content"]
    ), "File content is missing or empty"


def test_edit_tool(auth_setup, create_folder_setup, create_doc_setup):
    test_doc_id = global_state.get("test_doc_id")
    is_authenticated = global_state.get(
        "middleware.GoogleAuthMiddleware.is_authenticated"
    )
    assert is_authenticated, "Not authenticated"

    # Edit the document
    edit_response = edit_document_tool(
        document_id=test_doc_id,
        new_content="document was edited by test_get_edit_doc_tool",
    )

    assert isinstance(
        edit_response, dict
    ), "edit_document_tool should return a dictionary"
    assert (
        edit_response.get("status") == "success"
    ), f"Edit failed: {edit_response.get('error', edit_response)}"
