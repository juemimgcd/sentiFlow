from typing import Any

from pydantic import BaseModel, Field


class CommonResponse(BaseModel):
    code: int = Field(default=0)
    message: str = Field(default="success")
    data: Any = None