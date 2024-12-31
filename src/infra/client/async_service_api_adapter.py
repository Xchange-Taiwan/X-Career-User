import functools
from fastapi import status
from typing import Dict, Optional
import httpx
from ..template.service_response import ServiceApiResponse
from ..template.service_api import IServiceApi
from ...config.exception import *
import logging


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


SUCCESS_CODE = "0"


def check_response_code(method: str, expected_code: int = 200):
    def decorator_check_response_code(func):

        @functools.wraps(func)
        async def wrapper_check_response_code(*args, **kwargs):
            # request params
            function_name: str = func.__name__
            url = kwargs.get('url', args[1] if len(args) > 1 else None)
            params = kwargs.get('params', args[2] if len(args) > 2 else None)
            body = kwargs.get('json', args[2] if len(args) > 2 else None)
            headers = kwargs.get('headers', args[3] if len(args) > 3 else None)
            
            # response params
            status_code: int = 0
            code: str = ''
            msg: str = ''
            data: Dict = None

            service_api_res: ServiceApiResponse = await func(*args, **kwargs)
            status_code = service_api_res.status_code
            if status_code is not None and (status_code < 400 or status_code == expected_code):
                return service_api_res

            res_body = service_api_res.res_json
            code = res_body.get('code', None)
            msg = res_body.get('msg', None)
            data = res_body.get('data', None)

            log.error(
                f"service request fail, \n[%s]: %s, \nbody/params:%s, \nheaders:%s, \nstatus_code:%s, \nerr_msg: %s \n response:%s",
                method, url, body or params, headers, status_code, msg, res_body)
            raise_http_exception_by_status_code(status_code, msg, data)

        return wrapper_check_response_code

    return decorator_check_response_code


class AsyncServiceApiAdapter(IServiceApi):

    """
    return response body only
    """
    async def simple_get(self, url: str, params: Dict = None, headers: Dict = None) -> Optional[Dict[str, Any]]:
        service_api_response: ServiceApiResponse = await self.get(url, params, headers)
        if service_api_response:
            return service_api_response.data
        return None

    @check_response_code('get', 200)
    async def get(self, url: str, params: Dict = None, headers: Dict = None) -> Optional[ServiceApiResponse]:
        result = None
        response = None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=headers)
                result = ServiceApiResponse.parse(response)

        except Exception as e:
            log.error(f"simple_get request error, url:%s, params:%s, headers:%s, resp:%s, err:%s",
                      url, params, headers, response, e.__str__())
            raise ServerException(msg='get_connection_error')

        return result

    """
    return response body only
    """
    async def simple_post(self, url: str, json: Dict, headers: Dict = None) -> Optional[Dict[str, Any]]:
        service_api_response: ServiceApiResponse = await self.post(url, json, headers)
        if service_api_response:
            return service_api_response.data
        return None

    @check_response_code('post', 201)
    async def post(self, url: str, json: Dict, headers: Dict = None) -> Optional[ServiceApiResponse]:
        result = None
        response = None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=json, headers=headers)
                result = ServiceApiResponse.parse(response)

        except Exception as e:
            log.error(f"simple_post request error, url:%s, json:%s, headers:%s, resp:%s, err:%s",
                      url, json, headers, response, e.__str__())
            raise ServerException(msg='post_connection_error')

        return result

    """
    return response body only
    """
    async def simple_put(self, url: str, json: Dict = None, headers: Dict = None) -> Optional[Dict[str, Any]]:
        service_api_response: ServiceApiResponse = await self.put(url, json, headers)
        if service_api_response:
            return service_api_response.data
        return None

    @check_response_code('put', 200)
    async def put(self, url: str, json: Dict = None, headers: Dict = None) -> Optional[ServiceApiResponse]:
        result = None
        response = None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(url, json=json, headers=headers)
                result = ServiceApiResponse.parse(response)

        except Exception as e:
            log.error(f"simple_put request error, url:%s, json:%s, headers:%s, resp:%s, err:%s",
                      url, json, headers, response, e.__str__())
            raise ServerException(msg='put_connection_error')

        return result

    """
    return response body only
    """
    async def simple_delete(self, url: str, params: Dict = None, headers: Dict = None) -> Optional[Dict[str, Any]]:
        service_api_response = await self.delete(url, params, headers)
        if service_api_response:
            return service_api_response.data
        return None

    @check_response_code('delete', 200)
    async def delete(self, url: str, params: Dict = None, headers: Dict = None) -> Optional[ServiceApiResponse]:
        result = None
        response = None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(url, params=params, headers=headers)
                result = ServiceApiResponse.parse(response)

        except Exception as e:
            log.error(f"simple_delete request error, url:%s, params:%s, headers:%s, resp:%s, err:%s",
                      url, params, headers, response, e.__str__())
            raise ServerException(msg='delete_connection_error')

        return result

_async_service_api_adapter = AsyncServiceApiAdapter()
