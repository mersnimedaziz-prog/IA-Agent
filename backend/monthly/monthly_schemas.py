from pydantic import BaseModel
from typing import Optional


class TargetRequest(BaseModel):
    month: str
    kpi_name: str
    target_value: float
    unit: str = "hours"
    comparison: str = ">="
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class CalculateRequest(BaseModel):
    month: str
    kpi_name: str = "monthly_total_hours"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
