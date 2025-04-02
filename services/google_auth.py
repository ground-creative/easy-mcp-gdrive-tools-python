import os, base64, json
from fastapi.templating import Jinja2Templates
from fastapi import Cookie
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from core.utils.logger import logger
from core.utils.config import config
from core.utils.env import EnvConfig
from core.utils.state import global_state
from app.utils.credentials import credentials_to_json

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = config.get("OAUTHLIB_INSECURE_TRANSPORT")
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = config.get("OAUTHLIB_RELAX_TOKEN_SCOPE")

templates_directory = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../templates")
)
templates = Jinja2Templates(directory=templates_directory)

router = APIRouter()


@router.get("/auth")
async def login(request: Request):
    return RedirectResponse(url="/auth/login")


@router.get("/auth/login")
async def login(request: Request, current_access_token: str = None):
    logger.info("User initiated login process.")

    # Prepare the state data
    state_data = {
        "current_access_token": current_access_token,
    }
    state_encoded = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

    # Prepare the flow for authorization
    flow = Flow.from_client_secrets_file(
        config.get("GOOGLE_OAUTH_CLIENT_SECRETS_FILE"),
        scopes=config.get("GOOGLE_OAUTH_SCOPES"),
        redirect_uri=f"{EnvConfig.get('APP_HOST')}/auth/callback",
    )

    # Generate the authorization URL with the state parameter
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        state=state_encoded,  # Include state here
        include_granted_scopes="true",
    )

    logger.info("Redirecting user to authorization URL.")
    return RedirectResponse(url=authorization_url)


@router.get("/auth/callback")
async def auth_callback(request: Request):
    logger.info("Handling authentication callback.")

    if "error" in request.query_params:
        error_message = request.query_params["error"]
        logger.error(f"Authentication failed: {error_message}")
        return RedirectResponse(url="/auth/login")

    try:
        # Retrieve and decode the state parameter
        state_encoded = request.query_params.get("state")
        current_access_token = None

        if state_encoded:
            # Decode the state parameter
            state_data = json.loads(base64.urlsafe_b64decode(state_encoded).decode())
            current_access_token = state_data.get("current_access_token")
        flow = Flow.from_client_secrets_file(
            config.get("GOOGLE_OAUTH_CLIENT_SECRETS_FILE"),
            scopes=config.get("GOOGLE_OAUTH_SCOPES"),
            redirect_uri=f"{EnvConfig.get('APP_HOST')}/auth/callback",
        )
        flow.fetch_token(authorization_response=str(request.url))
        credentials = flow.credentials
        credentials_json = credentials_to_json(credentials)
        user_id = None
        granted_scopes = credentials._granted_scopes

        if not all(
            scope in granted_scopes for scope in config.get("GOOGLE_OAUTH_SCOPES")
        ):
            logger.warning("Not all required scopes were granted.")
            return RedirectResponse(url="/auth/login")

        try:
            id_info = id_token.verify_oauth2_token(
                credentials.id_token, google_requests.Request(), credentials.client_id
            )
            user_id = id_info["sub"]
        except ValueError as e:
            logger.error(f"Invalid ID token: {str(e)}")
            return JSONResponse(content={"error": str(e)}, status_code=500)

        db_handler = global_state.get("db_handler")

        # If current_access_token is provided, delete the existing credentials
        if current_access_token:
            logger.info(
                f"Deleting credentials for access token: {current_access_token}"
            )

            if not credentials.refresh_token:
                old_credentials = db_handler.get_credentials(
                    user_id, by_access_token=False
                )
                credentials_json["refresh_token"] = old_credentials["credentials"][
                    "refresh_token"
                ]
                db_handler.delete_credentials(current_access_token, user_id)

        access_token = db_handler.insert_credentials(user_id, credentials_json)
        logger.info("User authenticated successfully, credentials saved to file.")

        # Store user_id in cookie
        response = RedirectResponse(url="/auth/authenticated")
        response.set_cookie(
            key="access_token", value=access_token, httponly=True
        )  # Set cookie
        return response

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.get("/auth/authenticated")
async def authenticated(request: Request, access_token: str = Cookie(None)):
    logger.info("User accessed the authenticated route.")

    if access_token is None:
        return RedirectResponse(url="/auth/login")

    db_handler = global_state.get("db_handler")
    credentials = db_handler.get_credentials(access_token)

    if not credentials:
        logger.warning("Credentials not found for access token.")
        return RedirectResponse(url="/auth/login")

    return templates.TemplateResponse(
        "authenticated.html",
        {
            "request": request,
            "encrypted_user_id": access_token,
            "logo_url": EnvConfig.get("SERVICES_LOGO_URL"),
            "favicon_url": EnvConfig.get("SERVICES_FAVICON_URL"),
            "mcp_server_url": f"{EnvConfig.get('MCP_SERVER_URL')}",
            "mcp_server_name": EnvConfig.get("SERVER_NAME"),
        },
    )


@router.get("/auth/reset-access-token")
async def authenticated(request: Request, access_token: str = Cookie(None)):
    logger.info("User accessed the reset access token route.")

    if access_token is None:
        return RedirectResponse(url="/auth/login")

    return RedirectResponse(url=f"/auth/login?current_access_token={access_token}")
