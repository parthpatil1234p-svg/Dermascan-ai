from datetime import datetime

from pydantic import BaseModel, ConfigDict

ALLOWED_AGE_GROUPS = (
    "Under 18",
    "18-25",
    "26-35",
    "36-45",
    "46-60",
    "Above 60",
    "Prefer not to say",
)


class UserPublic(BaseModel):
    id: str
    full_name: str
    email: str
    age_group: str | None = None
    location: str | None = None
    is_active: bool
    is_admin: bool = False
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
