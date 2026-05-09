from datetime import datetime

from pydantic import BaseModel


class TemplateProfileRead(BaseModel):
    id: int
    name: str
    original_filename: str
    file_path: str
    profile: dict
    created_at: datetime

    model_config = {"from_attributes": True}
