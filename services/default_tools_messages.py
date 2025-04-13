import json
from fastapi import APIRouter
from fastapi.responses import JSONResponse, RedirectResponse
from core.utils.logger import logger  # Use to add logging capabilities
from typing import Optional

router = APIRouter()

# Load the messages from the JSON file
with open("app/config/default_tools_messages.json", "r", encoding="utf-8") as f:
    messages = json.load(f)


@router.get("/default-tools-messages")
@router.get("/default-tools-messages/")
async def redirect_to_slash():
    return RedirectResponse(url="/default-tools-messages/en")


@router.get("/default-tools-messages/{lang}")
async def my_route(lang: Optional[str] = None):
    # Log the request
    logger.info(f"Received request for default tools messages with lang: {lang}")

    # If lang is not provided, default to "en"
    if lang is None:
        lang = "en"  # Default language

    # If lang is not found in messages, return an empty JSON
    if lang not in messages:
        return JSONResponse(content={})  # Return empty JSON

    # Return the entire JSON configuration for the selected language
    return JSONResponse(content=messages[lang])
