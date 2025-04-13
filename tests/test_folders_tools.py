import os
import sys
from core.utils.state import global_state
from app.tools.create_folder import gdrive_create_folder_tool
from app.tools.delete_item import gdrive_delete_item_tool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def test_create_and_delete(auth_setup):

    is_authenticated = global_state.get(
        "middleware.GoogleAuthMiddleware.is_authenticated"
    )
    assert is_authenticated, "Not authenticated"

    response = gdrive_create_folder_tool(folder_name="test_create_and_delete_folder")
    assert response["status"] == "success", "Failed to create folder"
    folder_id = response["data"]["id"]

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


def test_create_and_delete_sub(auth_setup, create_folder_setup):

    subfolder_id = global_state.get("test_folder_id")
    is_authenticated = global_state.get(
        "middleware.GoogleAuthMiddleware.is_authenticated"
    )
    assert is_authenticated, "Not authenticated"

    response = gdrive_create_folder_tool(
        folder_name="test_create_and_delete_subfolder", parent_id=subfolder_id
    )

    assert response["status"] == "success", "Failed to create folder"
    folder_id = response["data"]["id"]

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
