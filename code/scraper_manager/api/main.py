from fastapi import FastAPI
from routes.scraping_endpoints import router as scraping_router
from routes.auth_enpoints import router as auth_router

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    app = FastAPI()
    app.include_router(scraping_router)
    app.include_router(auth_router)

    return app

app = create_app()