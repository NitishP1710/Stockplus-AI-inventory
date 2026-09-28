import asyncio
import logging
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.controllers.products import router as products_router
from app.controllers.suggestions import router as suggestions_router
from app.database.seed import seed_demo_products
from app.database.session import AsyncSessionLocal, create_db_and_tables
from app.events.background import start_background_loop

app = FastAPI(title=settings.app_name, version='1.0.0')
logger = logging.getLogger(__name__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(',') if origin.strip()],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
async def startup_event() -> None:
    app.state.db_ready = False
    if settings.auto_init_db:
        try:
            create_db_and_tables()
            async with AsyncSessionLocal() as db:
                await seed_demo_products(db)
            app.state.db_ready = True
            await start_background_loop()
        except Exception as exc:
            logger.warning("Skipping database initialization during startup: %s", exc)


@app.get('/health')
async def health() -> dict[str, str]:
    return {'status': 'ok', 'service': settings.app_name, 'database_ready': str(getattr(app.state, 'db_ready', False)).lower()}


app.include_router(products_router, prefix='/api')
app.include_router(suggestions_router, prefix='/api')
