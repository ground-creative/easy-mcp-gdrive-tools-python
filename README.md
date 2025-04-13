# Eeasy MCP GDrive Tools

This is a set of tools for gdrive to be used with easy mcp server.<br>
https://github.com/ground-creative/easy-mcp-python

## Installation

1. Clone the repository from the root folder of the easy mcp installation:

```
git clone https://github.com/ground-creative/easy-mcp-gdrive-tools-python.git app
```

2. Install requirements:

```
pip install -r app/requirements.txt
```

3. Generate encryption key:

```
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

4. Add parameters to env file:

```
APP_HOST=http://localhost:8000
DB_PATH=storage/sqlite_credentials.db
CYPHER=Your Encryption Key Here
```

5. Add `client_secrets.json` in storage folder

6. Run the server:

```
# Run via fastapi wrapper
python3 run.py -s fastapi
```

## Available MCP Tools

The following tools are provided by this MCP server:

## Tools and Specifications

| Tool Name | Description | Parameters Required |
|---|---|---|
| Create Document | Creates a new Google Docs document with the specified content | title (str), content (str), parent_folder_id (Optional [str]) |
| Edit Document | Edits an existing Google Docs document with the specified content | document_id (str), new_content (str) |
| Create File | Creates a new text, JSON, or CSV file with the specified content and uploads it to Google Drive | title (str), content (str), file_type (str), parent_folder_id (Optional [str]) |
| Create Folder | Creates a new folder in Google Drive | folder_name (str), parent_id (Optional [str]) |
| Delete Item | Deletes a specified item (file or folder) from Google Drive with confirmation logic | file_id (str), confirmation_token (Optional [str]) |
| Get File Contents | Retrieves the contents of a file based on its type (Google Docs, Google Sheets, PDF, text, JSON, or CSV) | file_id (str) |
| Get Item Details | Retrieves information about a file or folder in Google Drive based on its ID | item_id (str) |
| Get Items | Lists all items in a specified Google Drive folder or the root directory if no folder ID is provided | folder_id (Optional [str]) |
| Move Item | Moves a file or folder to a new folder in Google Drive | item_id (str), new_parent_id (str) |
| Search Items by Name | Searches for files and folders in Google Drive by their name | name (str) |
| Add Rows to Spreadsheet | Adds content to an existing Google Sheets document | sheet_id (str), values (list) |
| Create Spreadsheet | Creates a new Google Sheets document with the specified title | title (str), parent_folder_id (Optional [str]) |
| Delete Rows from Spreadsheet | Deletes specified rows from an existing Google Sheets document | sheet_id (str), row_indices (list) |
| Edit Rows of Spreadsheet | Edits rows in an existing Google Sheets document | sheet_id (str), range_name (str), values (list) |

* Make sure you have granted the appropriate scopes for the application to perform the operations on the drive.
