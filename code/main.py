from fastapi import FastAPI
from scraper_manager.api.routes.scraping_endpoints import router as scraping_router
from scraper_manager.api.routes.auth_enpoints import router as auth_router
from dotenv import load_dotenv

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    load_dotenv()
    app = FastAPI()
    app.include_router(scraping_router)
    app.include_router(auth_router)

    return app

app = create_app()