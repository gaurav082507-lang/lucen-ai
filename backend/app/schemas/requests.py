from typing import Optional
from pydantic import BaseModel, Field


class ClaimMetadata(BaseModel):
    claim_date: Optional[str] = Field(None, description="ISO date claim was filed (e.g. 2026-09-12)")
    incident_date: Optional[str] = Field(None, description="ISO date incident occurred (e.g. 2026-09-10)")
    claimed_amount: Optional[float] = Field(None, description="Monetary claim amount declared by claimant")
    currency: Optional[str] = Field("INR", description="Currency code (e.g. INR, USD, EUR)")
    claimant_name: Optional[str] = Field(None, description="Name of the claimant")
