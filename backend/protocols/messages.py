from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class A2AMessage(BaseModel):
    id: str = Field(default_factory=lambda: f"msg-{uuid4().hex[:8]}")
    type: str
    sender: str
    recipient: str
    payload: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    trace_id: Optional[str] = None
