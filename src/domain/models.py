"""
Domain Models - Immutable data structures using Pydantic

This module defines the core data models used throughout the application.
All models are frozen (immutable) to ensure functional purity.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class TradeRecord(BaseModel):
    """
    원본 거래 데이터 레코드
    
    Attributes:
        date: YYYY-MM 형식의 날짜
        export_amount: 수출 금액 (0 이상)
    """
    model_config = ConfigDict(frozen=True)  # 불변성 보장
    
    date: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="YYYY-MM 형식")
    export_amount: float = Field(..., ge=0, description="수출 금액")


class AnalysisResult(BaseModel):
    """
    분석 결과 (MoM/YoY 포함)
    
    Attributes:
        date: YYYY-MM 형식의 날짜
        export_amount: 수출 금액
        export_mom: 전월 대비 증감률 (%)
        export_yoy: 전년 동월 대비 증감률 (%)
    """
    model_config = ConfigDict(frozen=True)
    
    date: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    export_amount: float = Field(..., ge=0)
    export_mom: Optional[float] = Field(default=None, description="MoM (%)")
    export_yoy: Optional[float] = Field(default=None, description="YoY (%)")


class BusinessMetrics(BaseModel):
    """
    영업 메트릭 (영업일수, 일평균 등)
    
    Attributes:
        date: YYYY-MM 형식의 날짜
        export_amount: 수출 금액
        business_days: 영업일수
        daily_avg: 일평균 수출액
        daily_avg_mom: 일평균 MoM (%)
        daily_avg_yoy: 일평균 YoY (%)
    """
    model_config = ConfigDict(frozen=True)
    
    date: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    export_amount: float = Field(..., ge=0)
    business_days: int = Field(..., ge=0, description="영업일수")
    daily_avg: float = Field(..., ge=0, description="일평균 수출액")
    daily_avg_mom: Optional[float] = Field(default=None, description="일평균 MoM (%)")
    daily_avg_yoy: Optional[float] = Field(default=None, description="일평균 YoY (%)")
