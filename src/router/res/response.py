from fastapi.responses import JSONResponse
from typing import Optional, Any, Dict
from pydantic import create_model, BaseModel

# ref: https://github.com/tiangolo/fastapi/issues/3737
def idempotent_response(route: str, model: Any) -> (Dict):
    responses: Dict = {
        200: {
            'model': create_model(route, code=(str, ...), msg=(str, ...), data=(model, ...))
        }
    }
    return responses


def post_response(route: str, model: Any) -> (Dict):
    responses: Dict = {
        201: {
            'model': create_model(route, code=(str, ...), msg=(str, ...), data=(model, ...))
        }
    }
    return responses


def res_success(data=None, msg='ok', code='0'):
    return JSONResponse(content={
        'code': code,
        'msg': msg,
        'data': data,
    })


def res_err_format(data=None, msg='error', code='1'):
    return {
        'code': code,
        'msg': msg,
        'data': data,
    }


class ResponseVO(BaseModel):
    code: str = '0'
    msg: str = 'ok'
    data: Optional[Any] = None


'''[delete-Any]'''


class DeleteVO(ResponseVO):
    data: Optional[bool] = None
