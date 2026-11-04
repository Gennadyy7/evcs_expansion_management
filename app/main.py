from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import text
import uvicorn

from app.api import api_router
from app.core.config import settings
from app.core.database import db_manager
from app.core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    logger.info('Application starting up')
    db_manager.init()
    try:
        yield
    finally:
        await db_manager.close()
        logger.info('Application shutting down')


app = FastAPI(
    lifespan=lifespan,
    title='EVCS Expansion Management',
    description='Electric vehicle charging station network development system.',
    version='0.1.0',
    root_path=settings.APP_ROOT_PATH,
    docs_url='/docs' if settings.DOCS_ENABLED else None,
    redoc_url='/redoc' if settings.DOCS_ENABLED else None,
    openapi_url='/openapi.json' if settings.DOCS_ENABLED else None,
)

_api_prefix = '' if settings.APP_ROOT_PATH else '/api'
app.include_router(api_router, prefix=_api_prefix)


@app.get('/', include_in_schema=False)
async def root() -> RedirectResponse:
    if not settings.DOCS_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    docs_path = f'{settings.APP_ROOT_PATH}/docs' if settings.APP_ROOT_PATH else '/docs'
    return RedirectResponse(url=docs_path, status_code=status.HTTP_302_FOUND)


@app.get('/health', response_model=dict[str, str])
async def health_check() -> dict[str, str]:
    logger.debug('Health check requested')
    try:
        async with db_manager.get_session() as session:
            await session.execute(text('SELECT 1'))
    except Exception as e:
        logger.error(f'Health check failed: {e}')
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Service unavailable',
        ) from e
    return {'status': 'ok'}


def main() -> None:
    logger.info(f'Starting server on {settings.APP_HOST}:{settings.APP_PORT}')
    uvicorn.run(
        'app.main:app',
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == '__main__':
    main()
