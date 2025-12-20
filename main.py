from src.config.logging_config import init_logging
log = init_logging()

import os
import asyncio

from fastapi import FastAPI, HTTPException, \
    APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

from src.config import exception
from src.router.v1 import (
    user,
    mentor, file_controller,
)
from src.infra.resource.manager import resource_manager

STAGE = os.environ.get('STAGE')
root_path = '/' if not STAGE else f'/{STAGE}'
app = FastAPI(title='X-Career: User', root_path=root_path)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.on_event('startup')
async def startup_event():
    # init global connection pool
    await resource_manager.initial()
    asyncio.create_task(resource_manager.keeping_probe())


@app.on_event('shutdown')
async def shutdown_event():
    # close connection pool
    await resource_manager.close()

router_v1 = APIRouter(prefix='/user-service/api/v1')
router_v1.include_router(user.router)
router_v1.include_router(mentor.router)
router_v1.include_router(file_controller.router)

app.include_router(router_v1)

exception.include_app(app)


@app.get('/user-service/{term}')
async def info(term: str):
    if term != 'yolo':
        raise HTTPException(
            status_code=418, detail='Oops! Wrong phrase. Guess again?')
    return JSONResponse(content={'mention': 'You only live once.'})

# Mangum Handler, this is so important
handler = Mangum(app)
