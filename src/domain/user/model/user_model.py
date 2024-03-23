import json
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel
from .common_model import ProfessionVO, InterestListVO
from ....config.constant import *
import logging as log

log.basicConfig(filemode='w', level=log.INFO)


class ProfileDTO(BaseModel):
    name: Optional[str]
    avator: Optional[str]
    timezone: Optional[int]
    industry: Optional[int]
    position: Optional[str]
    company: Optional[str]
    linkedin_profile: Optional[str]
    interested_positions: Optional[List[int]] = []
    skills: Optional[List[int]] = []
    topics: Optional[List[int]] = []


class ProfileVO(BaseModel):
    user_id: int
    name: Optional[str]
    avator: Optional[str]
    timezone: Optional[int]
    industry: Optional[ProfessionVO]
    position: Optional[str]
    company: Optional[str]
    linkedin_profile: Optional[str]
    interested_positions: Optional[List[InterestListVO]] = []
    skills: Optional[List[InterestListVO]] = []
    topics: Optional[List[InterestListVO]] = []
