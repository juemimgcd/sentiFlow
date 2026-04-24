from fastapi.encoders import jsonable_encoder
from fastapi import status
from fastapi.responses import JSONResponse
from typing import Any


def success_response(message: str = "success", code: int = 0, data: Any = None, ):
    content = {
        "message": message,
        "data": data,
        "code":code
    }

    return JSONResponse(content=jsonable_encoder(content))



def error_response(message: str = "error", code: int = 1, data: Any = None, ):
    content = {
        "message": message,
        "data": data,
        "code":code

    }

    return JSONResponse(content=jsonable_encoder(content))
