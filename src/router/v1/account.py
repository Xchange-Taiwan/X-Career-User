import logging

from fastapi import APIRouter, Depends, Path, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..res.response import res_success
from ...app.account.delete import DeleteAccount
from ...domain.user.service.delete_account_service import DeleteAccountService
from ...infra.databse import db_session
from ...app._di.injection import (
    get_delete_account_service,
    get_delete_account_app,
)

log = logging.getLogger(__name__)

router = APIRouter(
    prefix='/internal/users',
    tags=['Internal - Account'],
    responses={404: {'description': 'Not found'}},
)


@router.get('/{user_id}/has-active-reservations')
async def has_active_reservations(
    user_id: int = Path(...),
    db: AsyncSession = Depends(db_session),
    service: DeleteAccountService = Depends(get_delete_account_service),
):
    has_active = await service.has_active_or_future_reservations(db, user_id)
    return res_success(data={"has_active": has_active})


@router.delete('/{user_id}', status_code=204)
async def delete_user_account(
    user_id: int = Path(...),
    db: AsyncSession = Depends(db_session),
    delete_account_app: DeleteAccount = Depends(get_delete_account_app),
):
    await delete_account_app.execute(db, user_id)
    return Response(status_code=204)
