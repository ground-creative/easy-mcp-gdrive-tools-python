import importlib
from core.utils.env import EnvConfig

SERVICES = [
    "core.services.server_info",  # server info html page
    "app.services.google_auth",
    "app.services.default_tools_messages",
]

INFO_SERVICE_CONFIG = {
    "service_uri": "/",
    "login_url": f"{EnvConfig.get('APP_HOST')}/auth/login",
    "site_url": EnvConfig.get("SITE_URL"),
    "site_name": EnvConfig.get("SITE_NAME"),
    "show_tools_specs": True,
    "header_params": {
        "X-ACCESS-TOKEN": "(Required) The access token for authenticating with the services, you can get one once you are authenticated via the login process."
    },
    "notes": [
        "- Ensure that the appropriate scopes are enabled in the Google authentication page for the services in use.",
        "- All tools that perform delete actions require confirmation. This is an experimental feature. Instruct the language model to prompt the user for confirmation for it to work effectively.",
    ],
}

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

GOOGLE_OAUTH_CLIENT_SECRETS_FILE = "storage/client_secrets.json"

GOOGLE_OAUTH_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
]

OAUTHLIB_INSECURE_TRANSPORT = "1"
OAUTHLIB_RELAX_TOKEN_SCOPE = "1"
