import json
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    Path, Body
)
import logging as log

from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from ..res.response import *
from ...domain.file.model.file_model import FileInfoDTO, FileInfoVO, FileInfoListVO
from ...domain.file.service.file_service import FileService
from ...infra.databse import get_db
from ...infra.util.injection_util import get_file_service

log.basicConfig(filemode='w', level=log.INFO)

router = APIRouter(
    prefix='/file',
    tags=['file'],
    responses={404: {'description': 'Not found'}},
)


@router.post('/create',
             responses=idempotent_response('create_file_info', FileInfoVO))
async def create_file_info(
        db: AsyncSession = Depends(get_db),
        body: FileInfoDTO = Body(...),
        file_service: FileService = Depends(get_file_service)
):
    res: FileInfoVO = await file_service.save_file_info(db, body)
    return res_success(data=jsonable_encoder(res))


@router.get('/{user_id}/{file_id}',
            responses=idempotent_response('get_file_info_by_id', FileInfoVO))
async def get_file_info_by_id(
        db: AsyncSession = Depends(get_db),
        user_id: int = Path(...),
        file_id: str = Path(...),
        file_service: FileService = Depends(get_file_service)
):
    res: FileInfoVO = await file_service.get_file_info(db, user_id, file_id)
    return res_success(data=jsonable_encoder(res))


@router.delete('/{user_id}/{file_id}',
               responses=idempotent_response('delete_file_info_by_id', bool))
async def delete_file_info_by_id(
        db: AsyncSession = Depends(get_db),
        user_id: int = Path(...),
        file_id: str = Path(...),
        file_service: FileService = Depends(get_file_service)
):
    res: bool = await file_service.delete_file_info(db, user_id, file_id)
    return res_success(data=res)


@router.get('/{user_id}',
            responses=idempotent_response('get_file_info_by_user_id', List[FileInfoVO]))
async def get_file_info_by_by_user_id(
        db: AsyncSession = Depends(get_db),
        user_id: int = Path(...),
        file_service: FileService = Depends(get_file_service)
):
    res: FileInfoListVO = await file_service.get_file_info_by_user_id(db, user_id)

    return res_success(data=jsonable_encoder(res))


@router.put('/{user_id}/update',
            responses=idempotent_response('update_file_info', FileInfoVO))
async def update_file_info(
        db: AsyncSession = Depends(get_db),
        user_id: int = Path(...),
        body: FileInfoDTO = Body(...),
        file_service: FileService = Depends(get_file_service)
):
    res: FileInfoVO = await file_service.update_file_info(db, user_id, body)
    return res_success(data=jsonable_encoder(res))
