import json
from typing import Dict, Optional, List, Union
from .client_response import ClientResponse
import httpx


class ServiceApiResponse(ClientResponse):
    data: Optional[Union[Dict, List, bool]] = None

    @staticmethod
    def parse(response: httpx.Response = None) -> 'ServiceApiResponse':
        if response:
            parsed_data = response.json()
            raw_data = parsed_data.get('data', {})
            # Ensure `data` is parsed properly
            if isinstance(raw_data, str):
                try:
                    data = json.loads(raw_data)
                except json.JSONDecodeError:
                    data = raw_data  # only a string
            else:
                data = raw_data
            return ServiceApiResponse(
                status_code=response.status_code,
                headers=response.headers,
                res_json=parsed_data,
                res_content=response.content,
                res_text=response.text,
                data=data
            )

        return None
