from src.domain.user.model.reservation_model import (
    ReservationQueryDTO,
    ReservationInfoVO,
    ReservationInfoListVO,
)
from src.domain.user.service.reservation_service import ReservationService

class ReservationList:
    def __init__(self, reservation_service: ReservationService):
        self.reservation_service = reservation_service

    async def list(self, db, query_dto: ReservationQueryDTO) -> ReservationInfoListVO:
        return

'''
ScaleOutReservationList 用來處理跨 DB 的預約列表
'''
class ScaleOutReservationList:
    pass


'''
CrossRegionReservationList 用來處理跨地區的預約列表
'''
class CrossRegionReservationList:
    pass
