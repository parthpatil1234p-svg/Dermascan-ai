from datetime import datetime
from typing import Literal

from pydantic import BaseModel

RoutineStatus = Literal["completed", "completed_with_limitations"]


class RoutineStep(BaseModel):
    step_number: int
    category: str
    product_id: str
    product_name: str
    brand_name: str
    purpose: str
    usage_guidance: str
    why_selected: str
    cautions: list[str]
    is_optional: bool
    is_demo_product: bool


class RoutineAlternative(BaseModel):
    category: str
    product_id: str
    product_name: str
    brand_name: str
    guidance: str
    cautions: list[str]
    is_demo_product: bool


class SkincareRoutineResponse(BaseModel):
    routine_report_id: str
    upload_id: str
    routine_status: RoutineStatus
    morning_routine: list[RoutineStep]
    night_routine: list[RoutineStep]
    optional_products: list[RoutineAlternative]
    warnings: list[str]
    limitations: list[str]
    routine_engine_version: str
    can_continue: bool
    next_route: str
    created_at: datetime
    updated_at: datetime
