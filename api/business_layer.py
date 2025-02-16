from pydantic import BaseModel, Field

class RequestBody(BaseModel):
    # required for all AI models
    vehicle_model: int = 2014
    # Model specific
    vehicle_make: str = "Yamaha"
    vehicle_line: str = "N-Max"
    kilometraje: int =  50000
    cilindraje: int = 200
    #location_state: str = "Bogotá D.C."


class ResponseBody(BaseModel):
    expected_price: float
    request_body: dict
    prediction_time_ms: float
