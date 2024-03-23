from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Any
from ..router.res.response import res_err_format
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class ErrorLogger:
    def __init__(self, msg: str):
        log.error(msg)
        


class ClientException(HTTPException, ErrorLogger):
    def __init__(self, msg: str, code: str = '40000', data: Any = None):
        self.msg = msg
        self.code = code
        self.data = data
        self.status_code = status.HTTP_400_BAD_REQUEST
        
    def __str__(self) -> str:
        return self.msg
        
class UnauthorizedException(HTTPException, ErrorLogger):
    def __init__(self, msg: str, code: str = '40100', data: Any = None):
        self.msg = msg
        self.code = code
        self.data = data
        self.status_code = status.HTTP_401_UNAUTHORIZED
        
    def __str__(self) -> str:
        return self.msg

class ForbiddenException(HTTPException, ErrorLogger):
    def __init__(self, msg: str, code: str = '40300', data: Any = None):
        self.msg = msg
        self.code = code
        self.data = data
        self.status_code = status.HTTP_403_FORBIDDEN
        
    def __str__(self) -> str:
        return self.msg

class NotFoundException(HTTPException, ErrorLogger):
    def __init__(self, msg: str, code: str = '40400', data: Any = None):
        self.msg = msg
        self.code = code
        self.data = data
        self.status_code = status.HTTP_404_NOT_FOUND
        
    def __str__(self) -> str:
        return self.msg
        
class NotAcceptableException(HTTPException, ErrorLogger):
    def __init__(self, msg: str, code: str = '40600', data: Any = None):
        self.msg = msg
        self.code = code
        self.data = data
        self.status_code = status.HTTP_406_NOT_ACCEPTABLE
        
    def __str__(self) -> str:
        return self.msg

class DuplicateUserException(HTTPException, ErrorLogger):
    def __init__(self, msg: str, code: str = '40600', data: Any = None):
        self.msg = msg
        self.code = code
        self.data = data
        self.status_code = status.HTTP_406_NOT_ACCEPTABLE
        
    def __str__(self) -> str:
        return self.msg
        
class TooManyRequestsException(HTTPException, ErrorLogger):
    def __init__(self, msg: str, code: str = '42900', data: Any = None):
        self.msg = msg
        self.code = code
        self.data = data
        self.status_code = status.HTTP_429_TOO_MANY_REQUESTS
        
    def __str__(self) -> str:
        return self.msg
        
class ServerException(HTTPException, ErrorLogger):
    def __init__(self, msg: str, code: str = '50000', data: Any = None):
        self.msg = msg
        self.code = code
        self.data = data
        self.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
    def __str__(self) -> str:
        return self.msg


def __client_exception_handler(request: Request, exc: ClientException):
    return JSONResponse(status_code=exc.status_code, content=res_err_format(msg=exc.msg, code=exc.code, data=exc.data))

def __unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    return JSONResponse(status_code=exc.status_code, content=res_err_format(msg=exc.msg, code=exc.code, data=exc.data))

def __forbidden_exception_handler(request: Request, exc: ForbiddenException):
    return JSONResponse(status_code=exc.status_code, content=res_err_format(msg=exc.msg, code=exc.code, data=exc.data))

def __not_found_exception_handler(request: Request, exc: NotFoundException):
    return JSONResponse(status_code=exc.status_code, content=res_err_format(msg=exc.msg, code=exc.code, data=exc.data))

def __not_acceptable_exception_handler(request: Request, exc: NotAcceptableException):
    return JSONResponse(status_code=exc.status_code, content=res_err_format(msg=exc.msg, code=exc.code, data=exc.data))

def __duplicate_user_exception_handler(request: Request, exc: DuplicateUserException):
    return JSONResponse(status_code=exc.status_code, content=res_err_format(msg=exc.msg, code=exc.code, data=exc.data))

def __too_many_requests_exception_handler(request: Request, exc: TooManyRequestsException):
    return JSONResponse(status_code=exc.status_code, content=res_err_format(msg=exc.msg, code=exc.code, data=exc.data))

def __server_exception_handler(request: Request, exc: ServerException):
    return JSONResponse(status_code=exc.status_code, content=res_err_format(msg=exc.msg, code=exc.code, data=exc.data))




def include_app(app: FastAPI):
    app.add_exception_handler(ClientException, __client_exception_handler)
    app.add_exception_handler(UnauthorizedException, __unauthorized_exception_handler)
    app.add_exception_handler(ForbiddenException, __forbidden_exception_handler)
    app.add_exception_handler(NotFoundException, __not_found_exception_handler)
    app.add_exception_handler(NotAcceptableException, __not_acceptable_exception_handler)
    app.add_exception_handler(DuplicateUserException, __duplicate_user_exception_handler)
    app.add_exception_handler(TooManyRequestsException, __too_many_requests_exception_handler)
    app.add_exception_handler(ServerException, __server_exception_handler)

def raise_http_exception(e: Exception, msg: str = None):
    if isinstance(e, ClientException):
        raise ClientException(msg=msg or e.msg, data=e.data)
    
    if isinstance(e, UnauthorizedException):
        raise UnauthorizedException(msg=msg or e.msg, data=e.data)
    
    if isinstance(e, ForbiddenException):
        raise ForbiddenException(msg=msg or e.msg, data=e.data)
        
    if isinstance(e, NotFoundException):
        raise NotFoundException(msg=msg or e.msg, data=e.data)
    
    if isinstance(e, NotAcceptableException):
        raise NotAcceptableException(msg=msg or e.msg, data=e.data)
    
    if isinstance(e, DuplicateUserException):
        raise DuplicateUserException(msg=msg or e.msg, data=e.data)
    
    if isinstance(e, ServerException):
        raise ServerException(msg=msg or e.msg, data=e.data)
    
    raise ServerException(msg=msg)
