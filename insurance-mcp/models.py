from pydantic import BaseModel
from typing import Literal, Optional

class BioData(BaseModel):
    age: int
    sex: Literal["female", "male"]
    bmi: float
    children: int
    smoker: Literal["yes", "no"]
    region: Literal["southeast", "northwest", "other"]

class BusinessProfile(BaseModel):
    business_size: Optional[int] = None
    location: Optional[str] = None
    coverage_preference: Optional[Literal["National", "Local"]] = None


