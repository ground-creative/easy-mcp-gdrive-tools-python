from core.utils.logger import logger
from core.utils.state import global_state  # Import global state
from core.utils.env import EnvConfig
from cryptography.fernet import Fernet
from googleapiclient.discovery import build


def decode_access_token(access_token: str):
    """Decode the access token to retrieve the original user ID."""
    # Retrieve the encryption key from environment variables
    encryption_key = EnvConfig.get("CYPHER").encode()  # Ensure it's in bytes

    # Create a Fernet instance with the encryption key
    fernet = Fernet(encryption_key)

    try:
        # Decrypt the access token
        decrypted_user_id = fernet.decrypt(access_token.encode()).decode()
        return decrypted_user_id  # Return the original user ID
    except Exception as e:
        # Handle decryption errors
        logger.error(f"Failed to decode access token: {str(e)}")
        return None  # Return None or handle as needed


def credentials_to_json(credentials):
    """Convert credentials to a JSON serializable format."""
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }


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
