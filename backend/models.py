"""Pydantic models and enums for the AgriChain API."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    HARVEST = "HARVEST"
    QUALITY_CHECK = "QUALITY_CHECK"
    TRANSPORT = "TRANSPORT"
    WAREHOUSE_ENTRY = "WAREHOUSE_ENTRY"
    PROCESSING = "PROCESSING"
    DISTRIBUTION = "DISTRIBUTION"
    RETAIL = "RETAIL"
    DOCUMENT = "DOCUMENT"


class Role(str, Enum):
    FARMER = "FARMER"
    COLLECTION_CENTER = "COLLECTION_CENTER"
    QUALITY_INSPECTOR = "QUALITY_INSPECTOR"
    TRANSPORTER = "TRANSPORTER"
    WAREHOUSE = "WAREHOUSE"
    PROCESSOR = "PROCESSOR"
    DISTRIBUTOR = "DISTRIBUTOR"
    RETAILER = "RETAILER"
    CONSUMER = "CONSUMER"
    REGULATOR = "REGULATOR"
    ADMINISTRATOR = "ADMINISTRATOR"


# --- Requests --------------------------------------------------------------
class ProductRegistration(BaseModel):
    crop: str = Field(..., examples=["Rice"])
    farmer: str = Field(..., examples=["Farmer_001"])
    location: str = Field(..., examples=["Konaseema"])
    quantity_kg: float = Field(..., gt=0, examples=[2500])
    quality_grade: str = Field(default="A", examples=["A"])
    variety: Optional[str] = Field(default=None, examples=["BPT-5204"])
    harvest_date: Optional[str] = Field(default=None, examples=["2026-08-10"])


class SupplyChainEvent(BaseModel):
    batch_id: str
    event_type: EventType
    actor_id: str
    location: str
    timestamp: Optional[str] = None
    data: dict[str, Any] = Field(default_factory=dict)


class SensorReading(BaseModel):
    batch_id: str
    temperature: float
    humidity: float
    gps_lat: float = 16.58
    gps_lon: float = 82.00
    timestamp: Optional[str] = None


class RiskInput(BaseModel):
    temperature: float
    humidity: float
    delay_hours: float
    quality_score: float
    quantity_kg: float = 2000
    transport_distance_km: float = 80


# --- Responses -------------------------------------------------------------
class RegistrationResponse(BaseModel):
    message: str
    batch_id: str
    block_index: int
    block_hash: str


class EventResponse(BaseModel):
    message: str
    block_index: int
    block_hash: str


class VerifyResponse(BaseModel):
    valid: bool
    message: str
    blocks: int


class RiskResult(BaseModel):
    score: int
    level: str
    factors: dict[str, int]
    ml_prediction: Optional[str] = None


class StatsResponse(BaseModel):
    total_batches: int
    verified: int
    flagged: int
    high_risk: int
    quality_failures: int
    temperature_alerts: int
    total_blocks: int
    chain_valid: bool
