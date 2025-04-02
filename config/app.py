import importlib

SERVICES = [
    "core.services.server_info",  # server info html page
    "app.services.google_auth",
]

PRESTART_HOOKS = {
    "fastapi": ["app.middleware.google.database.init_db"],
}

MIDDLEWARE = {
    "mcp": [
        {
            "middleware": "app.middleware.google.GoogleAuthMiddleware",
            "priority": 1,
            "args": {
                "auth_callback": lambda: getattr(
                    importlib.import_module(
                        "app.utils.credentials.attach_google_services".rsplit(".", 1)[0]
                    ),
                    "app.utils.credentials.attach_google_services".rsplit(".", 1)[-1],
                )
            },
        }
    ]
}

GOOGLE_OAUTH_CLIENT_SECRETS_FILE = "storage/config/client_secrets.json"

GOOGLE_OAUTH_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
]

OAUTHLIB_INSECURE_TRANSPORT = "1"
OAUTHLIB_RELAX_TOKEN_SCOPE = "1"
