from fastapi.routing import APIRouter
from fastapi import Path
from typing import Annotated

router = APIRouter(tags=["Authentication"], prefix="/auth")


@router.get("{username}")
def get_user(username: Annotated[str, Path(title="Username", description="The username of the user to get")]):
    """
    Get user by username.
    """
    return {"username": username}
