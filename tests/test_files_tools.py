import os
import sys
from core.utils.state import global_state
from app.tools.create_file import gdrive_create_file_tool
from app.tools.delete_item import gdrive_delete_item_tool


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def test_create_and_delete_text(auth_setup):

    is_authenticated = global_state.get(
        "middleware.GoogleAuthMiddleware.is_authenticated"
    )
    assert is_authenticated, "Not authenticated"

    response = gdrive_create_file_tool(
        title="test_create_and_delete_text",
        content="testing mcp server",
        file_type="text",
    )
    assert response["status"] == "success", "Failed to create file"
    file_id = response["file_id"]

    delete_response = gdrive_delete_item_tool(file_id=file_id)

    # Assert that the confirmation token is returned
    assert (
        "confirmation_token" in delete_response
    ), "No confirmation token received for deletion"

    confirmation_token = delete_response["confirmation_token"]

    # Now confirm the deletion using the received confirmation token
    final_delete_response = gdrive_delete_item_tool(
        file_id=file_id, confirmation_token=confirmation_token
    )

    # Assert the deletion was successful
    assert (
        final_delete_response["status"] == "success"
    ), "Failed to delete folder after confirmation"


def test_create_and_delete_sub(auth_setup, create_folder_setup):

    is_authenticated = global_state.get(
        "middleware.GoogleAuthMiddleware.is_authenticated"
    )
    assert is_authenticated, "Not authenticated"

    subfolder_id = global_state.get("test_folder_id")
    response = gdrive_create_file_tool(
        title="test_create_and_delete_sub",
        content="testing mcp server",
        file_type="text",
        parent_folder_id=subfolder_id,
    )
    assert response["status"] == "success", "Failed to create file"
    file_id = response["file_id"]

    delete_response = gdrive_delete_item_tool(file_id=file_id)

    # Assert that the confirmation token is returned
    assert (
        "confirmation_token" in delete_response
    ), "No confirmation token received for deletion"

    confirmation_token = delete_response["confirmation_token"]

    # Now confirm the deletion using the received confirmation token
    final_delete_response = gdrive_delete_item_tool(
        file_id=file_id, confirmation_token=confirmation_token
    )

    # Assert the deletion was successful
    assert (
        final_delete_response["status"] == "success"
    ), "Failed to delete folder after confirmation"


def test_create_and_delete_json(auth_setup):
    is_authenticated = global_state.get(
        "middleware.GoogleAuthMiddleware.is_authenticated"
    )
    assert is_authenticated, "Not authenticated"

    response = gdrive_create_file_tool(
        title="test_create_and_delete_json",
        content='{"message": "Hello, world!", "status": "ok"}',
        file_type="json",
    )
    assert response["status"] == "success", "Failed to create JSON file"
    file_id = response["file_id"]

    delete_response = gdrive_delete_item_tool(file_id=file_id)
    assert "confirmation_token" in delete_response, "No confirmation token received"

    confirmation_token = delete_response["confirmation_token"]
    final_delete_response = gdrive_delete_item_tool(
        file_id=file_id, confirmation_token=confirmation_token
    )
    assert final_delete_response["status"] == "success", "Failed to delete JSON file"


def test_create_and_delete_csv(auth_setup):
    is_authenticated = global_state.get(
        "middleware.GoogleAuthMiddleware.is_authenticated"
    )
    assert is_authenticated, "Not authenticated"

    response = gdrive_create_file_tool(
        title="test_create_and_delete_csv",
        content="name,age\nAlice,30\nBob,25",
        file_type="csv",
    )
    assert response["status"] == "success", "Failed to create CSV file"
    file_id = response["file_id"]

    delete_response = gdrive_delete_item_tool(file_id=file_id)
    assert "confirmation_token" in delete_response, "No confirmation token received"

    confirmation_token = delete_response["confirmation_token"]
    final_delete_response = gdrive_delete_item_tool(
        file_id=file_id, confirmation_token=confirmation_token
    )
    assert final_delete_response["status"] == "success", "Failed to delete CSV file"
