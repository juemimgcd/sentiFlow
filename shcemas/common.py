from typing import Any

from pydantic import BaseModel, Field


class CommonResponse(BaseModel):
    """统一接口响应结构，封装状态码、提示信息和业务数据。"""

    code: int = Field(default=0)
    message: str = Field(default="success")
    data: Any = None
