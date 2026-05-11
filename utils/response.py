from fastapi.encoders import jsonable_encoder
from fastapi import status
from fastapi.responses import JSONResponse
from typing import Any


# 构建统一的成功 JSON 响应。
def success_response(message: str = "success", code: int = 0, data: Any = None, ):
    content = {
        "message": message,
        "data": data,
        "code":code
    }

    return JSONResponse(content=jsonable_encoder(content))



# 构建统一的错误 JSON 响应。
def error_response(message: str = "error", code: int = 1, data: Any = None, ):
    content = {
        "message": message,
        "data": data,
        "code":code

    }

    return JSONResponse(content=jsonable_encoder(content))
