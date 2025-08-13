"""Pydantic models describing the backtest configuration file."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class Latency(BaseModel):
    inbound: int
    exchange: int
    outbound: int


class Fees(BaseModel):
    sec_per_million: float = Field(alias="sec_per_million")
    taf_per_share: float
    min_fee: float


class Execution(BaseModel):
    impact_coeff: float
    fill_queue_model: str
    partial_fills: bool
    extended_hours: bool


class Risk(BaseModel):
    mode: str
    pdt_enforced: bool


class BacktestConfig(BaseModel):
    start: date
    end: date
    bar_interval: str
    latency_ms: Latency
    fees: Fees
    execution: Execution
    risk: Risk
    marking: str
    universe: str
    seed: int

    @classmethod
    def from_yaml(cls, path: Path) -> BacktestConfig:
        data = yaml.safe_load(path.read_text())
        return cls.model_validate(data)
