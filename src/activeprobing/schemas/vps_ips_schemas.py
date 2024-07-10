from pydantic import BaseModel


class VpsIP(BaseModel):
    ip: str
    region: str
    service: str
