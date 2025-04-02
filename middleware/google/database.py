import sqlite3
import json
from cryptography.fernet import Fernet
from core.utils.logger import logger
from core.utils.state import global_state
from core.utils.env import EnvConfig


def init_db(server_name):
    encryption_key = EnvConfig.get("CYPHER")
    cipher = Fernet(encryption_key)
    db_path = EnvConfig.get("DB_PATH")
    db_handler = DatabaseHandler(db_path, cipher)
    global_state.set("db_handler", db_handler)
    logger.info("Database initialized successfully.")


class DatabaseHandler:
    """Class to handle database operations."""

    def __init__(self, db_path, cipher):
        self.db_path = db_path
        self.cipher = cipher
        self.initialize_db()

    def initialize_db(self):
        """Create the SQLite database and tables if they do not exist."""
        logger.info(
            f"Initializing database at: {self.db_path}"
        )  # Log database initialization
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create table for user credentials with access_token column
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_credentials (
                user_id TEXT PRIMARY KEY,
                credentials_json TEXT NOT NULL,
                access_token TEXT
            )
            """
        )

        conn.commit()
        cursor.close()
        conn.close()
        logger.info(
            "Database initialized successfully."
        )  # Log successful initialization

    def insert_credentials(self, user_id: str, credentials_json: dict):
        """Insert encrypted JSON credentials into the database."""
        logger.info(
            f"Inserting credentials for user_id: {user_id}"
        )  # Log credential insertion

        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if the user already exists to retrieve the existing access token
        cursor.execute(
            "SELECT access_token, credentials_json FROM user_credentials WHERE user_id = ?",
            (user_id,),
        )
        existing_credentials = cursor.fetchone()

        if existing_credentials:
            # If the user exists, retrieve the existing access token and credentials using named access
            access_token = existing_credentials["access_token"]  # Access by column name
            existing_credentials_json = json.loads(
                self.cipher.decrypt(existing_credentials["credentials_json"]).decode()
            )
            credentials_json["refresh_token"] = (
                credentials_json["refresh_token"]
                if credentials_json["refresh_token"]
                else existing_credentials_json.get("refresh_token")
            )
            logger.info(f"Existing credentials found for user_id: {user_id}.")
        else:
            # Generate a new access token
            access_token = (
                Fernet(EnvConfig.get("CYPHER").encode())
                .encrypt(user_id.encode())
                .decode()
            )
            logger.info(
                f"No existing credentials found for user_id: {user_id}. Generated new access token."
            )

        encrypted_credentials = self.cipher.encrypt(
            json.dumps(credentials_json).encode()
        )

        # Insert or update the credentials in the database
        cursor.execute(
            """
            INSERT INTO user_credentials (user_id, credentials_json, access_token)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET 
                credentials_json = excluded.credentials_json,
                access_token = access_token;  -- Keep existing access token
            """,
            (user_id, encrypted_credentials, access_token),
        )

        conn.commit()
        cursor.close()
        conn.close()
        logger.info(
            f"Credentials for user_id: {user_id} inserted/updated successfully."
        )  # Log success

        return access_token  # Return the access token (existing or new)

    def get_credentials(self, identifier: str, by_access_token: bool = True):
        """Retrieve and decrypt JSON credentials based on access token or user ID."""
        if by_access_token:
            logger.info(
                f"Retrieving credentials for access_token: {identifier}"
            )  # Log credential retrieval
            query = "SELECT credentials_json, access_token, user_id FROM user_credentials WHERE access_token = ?;"
            params = (identifier,)
        else:
            logger.info(
                f"Retrieving credentials for user_id: {identifier}"
            )  # Log credential retrieval
            query = "SELECT credentials_json, access_token FROM user_credentials WHERE user_id = ?;"
            params = (identifier,)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(query, params)
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result:
            encrypted_credentials = result[0]
            decrypted_credentials = json.loads(
                self.cipher.decrypt(encrypted_credentials).decode()
            )
            access_token = result[1]  # Retrieve access token
            user_id = (
                result[2] if by_access_token else identifier
            )  # Get user_id if searching by access token
            logger.info(
                f"Credentials retrieved successfully for identifier: {identifier}"
            )  # Log success
            return {
                "user_id": user_id,
                "credentials": decrypted_credentials,
                "access_token": access_token,
            }
        else:
            logger.warning(
                f"User ID not found: {identifier}"
            )  # Log warning for not found
            return {"error": "User ID not found."}

    def delete_credentials(self, access_token: str, user_id: str):
        """Delete credentials from the database based on access token and user ID."""
        logger.info(
            f"Attempting to delete credentials for access_token: {access_token} and user_id: {user_id}"
        )  # Log credential deletion attempt

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Delete the credentials using both access_token and user_id
        cursor.execute(
            "DELETE FROM user_credentials WHERE access_token = ? AND user_id = ?;",
            (access_token, user_id),
        )

        conn.commit()

        # Check if any rows were deleted
        if cursor.rowcount > 0:
            logger.info(
                f"Credentials for user_id: {user_id} deleted successfully."
            )  # Log success
        else:
            logger.warning(
                f"No credentials found for access_token: {access_token} and user_id: {user_id}"
            )  # Log warning for not found

        cursor.close()
        conn.close()

    def update_access_token(self, user_id: str, new_access_token: str):
        """Update the access token in the credentials_json for a specific user in the database."""
        logger.info(
            f"Updating access token for user_id: {user_id}"
        )  # Log the update attempt

        # Connect to the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Retrieve existing credentials
        cursor.execute(
            "SELECT credentials_json FROM user_credentials WHERE user_id = ?;",
            (user_id,),
        )
        result = cursor.fetchone()

        if result:
            # Decrypt existing credentials
            encrypted_credentials = result[0]
            decrypted_credentials = json.loads(
                self.cipher.decrypt(encrypted_credentials).decode()
            )

            # Update the access token in the credentials JSON
            decrypted_credentials["access_token"] = new_access_token

            # Encrypt the updated credentials
            updated_encrypted_credentials = self.cipher.encrypt(
                json.dumps(decrypted_credentials).encode()
            )

            # Update the credentials in the database
            cursor.execute(
                """
                UPDATE user_credentials
                SET credentials_json = ?
                WHERE user_id = ?;
                """,
                (updated_encrypted_credentials, user_id),
            )

            conn.commit()
            logger.info(
                f"Access token updated successfully for user_id: {user_id}."
            )  # Log success
        else:
            logger.warning(
                f"No credentials found for user_id: {user_id}."
            )  # Log warning if not found

        cursor.close()
        conn.close()
