import os
import sys
from core.utils.state import global_state
from app.tools.create_sheet import create_sheet_tool
from app.tools.delete_item import delete_item_tool
from app.tools.add_rows_to_sheet import add_rows_tool
from app.tools.delete_rows_from_sheet import delete_rows_tool
from app.tools.edit_rows_of_sheet import edit_rows_tool
from app.tools.get_file_contents import get_file_contents_tool


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def test_create_and_delete(auth_setup):

    is_authenticated = global_state.get(
        "middleware.GoogleAuthMiddleware.is_authenticated"
    )
    assert is_authenticated, "Not authenticated"

    response = create_sheet_tool(title="test_create_and_delete_sheet")
    assert response["status"] == "success", "Failed to create folder"
    sheet_id = response["sheet_id"]

    delete_response = delete_item_tool(file_id=sheet_id)

    # Assert that the confirmation token is returned
    assert (
        "confirmation_token" in delete_response
    ), "No confirmation token received for deletion"

    confirmation_token = delete_response["confirmation_token"]

    # Now confirm the deletion using the received confirmation token
    final_delete_response = delete_item_tool(
        file_id=sheet_id, confirmation_token=confirmation_token
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

    response = create_sheet_tool(
        title="test_create_and_delete_sheet", parent_folder_id=subfolder_id
    )
    assert response["status"] == "success", "Failed to create folder"
    sheet_id = response["sheet_id"]

    delete_response = delete_item_tool(file_id=sheet_id)

    # Assert that the confirmation token is returned
    assert (
        "confirmation_token" in delete_response
    ), "No confirmation token received for deletion"

    confirmation_token = delete_response["confirmation_token"]

    # Now confirm the deletion using the received confirmation token
    final_delete_response = delete_item_tool(
        file_id=sheet_id, confirmation_token=confirmation_token
    )

    # Assert the deletion was successful
    assert (
        final_delete_response["status"] == "success"
    ), "Failed to delete folder after confirmation"


def test_add_edit_and_delete_rows(auth_setup, create_folder_setup, create_sheet_setup):

    is_authenticated = global_state.get(
        "middleware.GoogleAuthMiddleware.is_authenticated"
    )
    assert is_authenticated, "Not authenticated"

    test_sheet_id = global_state.get("test_sheet_id")
    response = add_rows_tool(
        sheet_id=test_sheet_id, values=[["1", "2", "3"], ["4", "5", "6"]]
    )

    assert response["status"] == "success", "Failed to add rows to sheet"

    response = edit_rows_tool(
        sheet_id=test_sheet_id,
        range_name="Sheet1!A1:C2",
        values=[["a", "b", "c"], ["d", "e", "f"]],
    )

    assert response["status"] == "success", "Failed to edit rows in sheet"

    response = delete_rows_tool(sheet_id=test_sheet_id, row_indices=[1, 2])

    assert response["status"] == "success", "Failed to delete rows from sheet"


def test_get_contents_tool(auth_setup, create_folder_setup, create_sheet_setup):
    test_sheet_id = global_state.get("test_sheet_id")
    is_authenticated = global_state.get(
        "middleware.GoogleAuthMiddleware.is_authenticated"
    )
    assert is_authenticated, "Not authenticated"

    response = get_file_contents_tool(file_id=test_sheet_id)

    assert (
        response["status"] == "success"
    ), f"Failed to fetch file: {response.get('error')}"
