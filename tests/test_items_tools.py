import os
import sys
from core.utils.state import global_state
from app.tools.get_items import get_items_tool
from app.tools.create_folder import create_folder_tool
from app.tools.delete_item import delete_item_tool
from app.tools.move_item import move_item_tool
from app.tools.get_item_details import get_item_details_tool
from app.tools.search_items_by_name import search_items_by_name_tool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def test_get_items_in_root_folder(auth_setup):

    is_authenticated = global_state.get(
        "middleware.GoogleAuthMiddleware.is_authenticated"
    )
    assert is_authenticated, "Not authenticated"

    response = get_items_tool()

    assert response["status"] == "success", "Failed to get items"
    assert isinstance(response["data"], list), "Return data is not a list"


def test_get_in_subfolder(auth_setup, create_folder_setup):
    subfolder_id = global_state.get("test_folder_id")
    is_authenticated = global_state.get(
        "middleware.GoogleAuthMiddleware.is_authenticated"
    )
    assert is_authenticated, "Not authenticated"

    response = get_items_tool(folder_id=subfolder_id)

    assert response["status"] == "success", "Failed to get items"
    assert isinstance(response["data"], list), "Return data is not a list"


def test_delete(auth_setup):

    is_authenticated = global_state.get(
        "middleware.GoogleAuthMiddleware.is_authenticated"
    )
    assert is_authenticated, "Not authenticated"

    response = create_folder_tool(folder_name="test_delete_item")
    assert response["status"] == "success", "Failed to create folder"
    folder_id = response["data"]["id"]

    delete_response = delete_item_tool(file_id=folder_id)

    # Assert that the confirmation token is returned
    assert (
        "confirmation_token" in delete_response
    ), "No confirmation token received for deletion"

    confirmation_token = delete_response["confirmation_token"]

    # Now confirm the deletion using the received confirmation token
    final_delete_response = delete_item_tool(
        file_id=folder_id, confirmation_token=confirmation_token
    )

    # Assert the deletion was successful
    assert (
        final_delete_response["status"] == "success"
    ), "Failed to delete folder after confirmation"


def test_move_tool(auth_setup, create_folder_setup):

    is_authenticated = global_state.get(
        "middleware.GoogleAuthMiddleware.is_authenticated"
    )
    assert is_authenticated, "Not authenticated"

    response = create_folder_tool(folder_name="test_move_item_tool")

    assert response["status"] == "success", "Failed to create folder"

    folder_id = response["data"]["id"]

    subfolder_id = global_state.get("test_folder_id")
    response = move_item_tool(item_id=folder_id, new_parent_id=subfolder_id)

    assert response["status"] == "success", f"Move failed: {response}"


def test_get_details_tool(auth_setup, create_folder_setup):

    is_authenticated = global_state.get(
        "middleware.GoogleAuthMiddleware.is_authenticated"
    )
    assert is_authenticated, "Not authenticated"

    subfolder_id = global_state.get("test_folder_id")
    response = get_item_details_tool(item_id=subfolder_id)

    assert response["status"] == "success", f"Failed to get item details: {response}"
    assert response["is_folder"] is True, "Item is not a folder"
    assert response["file_info"]["id"] == subfolder_id, "Item ID does not match"


def test_search_by_name_tool(auth_setup, create_folder_setup):
    test_folder_name = global_state.get("test_folder_name")

    response = search_items_by_name_tool(name=test_folder_name)

    assert response["status"] == "success", f"Search failed: {response.get('error')}"
    assert any(
        item["name"] == test_folder_name for item in response["files"]
    ), f"No matching item with title '{test_folder_name}' found in: {response['files']}"
