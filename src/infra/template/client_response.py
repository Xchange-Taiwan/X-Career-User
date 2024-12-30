from fastapi import status
from pydantic import BaseModel
from typing import Dict, Any
import httpx

class ClientResponse(BaseModel):

    status_code: int = status.HTTP_200_OK
    headers: Dict = None    # BaseModel 不支援 native dict, any
    # response body
    res_json: Dict = None   # BaseModel 不支援 native dict, any
    res_content: Any = None # BaseModel 不支援 native dict, any
    res_text: str = None


    @staticmethod
    def parse(response: httpx.Response = None) -> 'ClientResponse':
        if response:
            return ClientResponse(
                status_code=response.status_code,
                headers=response.headers,
                res_json=response.json(),
                res_content=response.content,
                res_text=response.text,
            )

        return None