from pydantic import BaseModel


class VpsIP(BaseModel):
    ip_prefix: str
    region: str
    service: str
