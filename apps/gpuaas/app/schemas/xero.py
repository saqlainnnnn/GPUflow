from pydantic import BaseModel


class XeroConnectionResponse(BaseModel):
    connected: bool
    tenant_id: str | None = None
    tenant_name: str | None = None


class XeroCallbackResponse(BaseModel):
    connected: bool
    tenant_id: str
    tenant_name: str | None = None
