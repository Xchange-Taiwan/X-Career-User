from fastapi import (
    APIRouter,
    Depends,
    Path, Body
)
import logging as log

from sqlalchemy.ext.asyncio import AsyncSession

from ..res.response import *
from ...domain.file.model.file_model import FileInfoDTO, FileInfoVO
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
    return res_success(data=res.json())


@router.get('/all',
            responses=idempotent_response('get_all_files_info', list[FileInfoVO]))
async def get_all_files(
        db: AsyncSession = Depends(get_db),
        file_service: FileService = Depends(get_file_service)
):
    res: list[FileInfoVO] = await file_service.get_all_files(db)
    return res_success(data=[r.json() for r in res])


@router.get('/{file_id}',
            responses=idempotent_response('get_file_info_by_id', FileInfoVO))
async def get_file_info(
        db: AsyncSession = Depends(get_db),
        file_id: str = Path(...),
        file_service: FileService = Depends(get_file_service)
):
    res: FileInfoVO = await file_service.get_file_info(db, file_id)
    return res_success(data=res.json())


@router.delete('/{file_id}',
               responses=idempotent_response('delete_file_info_by_id', bool))
async def delete_file_info(
        db: AsyncSession = Depends(get_db),
        file_id: str = Path(...),
        file_service: FileService = Depends(get_file_service)
):
    res: bool = await file_service.delete_file_info(db, file_id)
    return res_success(data=res)


@router.get('/name/{filename}',
            responses=idempotent_response('get_by_filename', FileInfoVO))
async def get_file_info_by_filename(
        db: AsyncSession = Depends(get_db),
        filename: str = Path(...),
        file_service: FileService = Depends(get_file_service)
):
    res: FileInfoVO = await file_service.get_file_info_by_filename(db, filename)
    return res_success(data=res.json())


@router.put('/update',
            responses=idempotent_response('update', FileInfoVO))
async def update_file_info(
        db: AsyncSession = Depends(get_db),
        body: FileInfoDTO = Body(...),
        file_service: FileService = Depends(get_file_service)
):
    res: FileInfoVO = await file_service.update_file_info(db, body)
    return res_success(data=res.json())
