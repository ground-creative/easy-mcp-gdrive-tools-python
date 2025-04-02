# Google Auth Middleware For Easy MCP Server

This is a google authentication service middleware for easy mcp python.

## Installation

1. Donwload middlewares from the root folder of the easy mcp installation:

```
wget
```

2. Create create a utility to attach credentials to global variables:

```
# app/utils/credentials.py

from core.utils.state import global_state
from googleapiclient.discovery import build

def attach_google_services(credentials):
    """Attach Google API services to the global state."""
    drive_service = build("drive", "v3", credentials=credentials)
    docs_service = build("docs", "v1", credentials=credentials)
    sheets_service = build("sheets", "v4", credentials=credentials)

    global_state.set(
        "google_drive_service", drive_service, True
    )  # Save Drive service to global state
    global_state.set(
        "google_docs_service", docs_service, True
    )  # Save Docs service to global state
    global_state.set(
        "google_sheets_service", sheets_service, True
    )  # Save Sheets service to global state
```

3. Create file app/config/app.py if it does not exists and add the the middleware:

```
MIDDLEWARE = {
    "mcp": [
        {
            "middleware": "app.middleware.google.GoogleAuthMiddleware",
            "priority": 1,
            "args": {"auth_callback": "app.utils.credentials.attach_google_services"},
        }
    ]
}
```

4. Install required dependencies:

```
# Add to requirements.txt in easy mcp root folder

google-auth-oauthlib==1.2.1
cryptography==44.0.2
google-api-python-client==2.166.0

# Run installer
pip install -r requirements.txt
```

## Usage

Refer to the database file for usage

## Version

1.0
