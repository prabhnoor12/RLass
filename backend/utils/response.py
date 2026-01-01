from fastapi.responses import JSONResponse
from typing import Any, Optional

def success_response(data: Any = None, message: Optional[str] = None, status_code: int = 200):
    response = {"success": True}
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    return JSONResponse(content=response, status_code=status_code)

def error_response(message: str, status_code: int = 400, data: Any = None):
    response = {"success": False, "message": message}
    if data is not None:
        response["data"] = data
    return JSONResponse(content=response, status_code=status_code)
