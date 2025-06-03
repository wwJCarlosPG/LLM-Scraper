from fastapi.routing import APIRouter
from fastapi import Path
from typing import Annotated
from scraper_manager.config.logging import logger
router = APIRouter(tags=["Authentication"], prefix="/auth")


@router.get("{username}")
def get_user(username: Annotated[str, Path(title="Username", description="The username of the user to get")]):
    """
    Get user by username.
    """
    logger.info(f"{username}")
    return {"username": username}
