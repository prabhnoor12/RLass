import pytest
import json
from fastapi.responses import JSONResponse
from backend.utils.response import success_response, error_response

def test_success_response_with_data_and_message():
    data = {"foo": "bar"}
    message = "Operation successful"
    status_code = 201
    response = success_response(data=data, message=message, status_code=status_code)
    assert isinstance(response, JSONResponse)
    assert response.status_code == status_code
    content = json.loads(response.body.decode())
    assert content["success"] is True
    assert content["data"] == data
    assert content["message"] == message

def test_success_response_without_data_or_message():
    response = success_response()
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    content = json.loads(response.body.decode())
    assert content["success"] is True
    assert "data" not in content
    assert "message" not in content

def test_error_response_with_message_and_data():
    message = "Something went wrong"
    data = {"error": "details"}
    status_code = 422
    response = error_response(message=message, status_code=status_code, data=data)
    assert isinstance(response, JSONResponse)
    assert response.status_code == status_code
    content = json.loads(response.body.decode())
    assert content["success"] is False
    assert content["message"] == message
    assert content["data"] == data

def test_error_response_with_message_only():
    message = "Error occurred"
    response = error_response(message=message)
    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    content = json.loads(response.body.decode())
    assert content["success"] is False
    assert content["message"] == message
    assert "data" not in content
