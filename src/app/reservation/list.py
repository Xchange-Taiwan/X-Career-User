from src.domain.user.model.reservation_model import *

class LocalReservationList:
    def __init__(self, reservation_service):
      self.reservation_service = reservation_service


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
