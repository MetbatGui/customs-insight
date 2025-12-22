"""
Domain Models - Immutable data structures using Pydantic

This module defines the core data models used throughout the application.
All models are frozen (immutable) to ensure functional purity.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Union, Literal



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


# ============= 필터 클래스 =============

class Filter(BaseModel):
    """필터 기본 클래스"""
    model_config = ConfigDict(frozen=True)
    category: str


class DomesticRegionFilter(Filter):
    """
    국내지역 필터
    
    TOML 매핑: category = "국내지역"
    
    Attributes:
        category: "국내지역" (자동 설정)
        scope: 지역 범위 ("시" 또는 "시군구")
        regions: 지역명 리스트
    """
    category: Literal["국내지역"] = "국내지역"
    scope: Literal["시", "시군구"] = Field(..., description="지역 범위")
    regions: List[str] = Field(..., min_length=1, description="지역명 리스트")


class CustomsOfficeFilter(Filter):
    """
    세관 필터
    
    TOML 매핑: category = "세관"
    
    Attributes:
        category: "세관" (자동 설정)
        customs_offices: 세관명 리스트
    """
    category: Literal["세관"] = "세관"
    customs_offices: List[str] = Field(..., min_length=1, description="세관명 리스트")


# ============= 전략 클래스 =============

class StrategyItem(BaseModel):
    """
    품목 전략
    
    TOML 매핑: [[corp.items]]
    
    Attributes:
        name: 품목명
        hs_code: 10자리 HS Code
        filters: 적용할 필터 목록
    """
    model_config = ConfigDict(frozen=True)
    
    name: str = Field(..., description="품목명")
    hs_code: str = Field(..., pattern=r"^\d{10}$", description="10자리 HS Code")
    filters: List[Union[DomesticRegionFilter, CustomsOfficeFilter]] = Field(
        default_factory=list,
        description="적용할 필터 목록"
    )


class Strategy(BaseModel):
    """
    전략 클래스
    
    TOML 매핑: [corp]
    
    Attributes:
        name: 회사명
        items: 품목 리스트
    
    Example:
        >>> import tomllib
        >>> with open("strategies/농심.toml", "rb") as f:
        ...     config = tomllib.load(f)
        >>> strategy = Strategy.from_toml_dict(config)
        >>> strategy.name
        '농심'
    """
    model_config = ConfigDict(frozen=True)
    
    name: str = Field(..., description="회사명")
    items: List[StrategyItem] = Field(..., min_length=1, description="품목 리스트")
    
    @classmethod
    def from_toml_dict(cls, toml_dict: dict) -> "Strategy":
        """
        TOML 딕셔너리를 Strategy 객체로 변환
        
        Args:
            toml_dict: tomllib.load()의 결과
            
        Returns:
            Strategy: 타입 검증된 Strategy 객체
            
        Raises:
            ValidationError: TOML 구조가 올바르지 않은 경우
            KeyError: 필수 키가 없는 경우
        """
        corp_data = toml_dict.get("corp", {})
        
        items_data = []
        for item in corp_data.get("items", []):
            filters = []
            for f in item.get("filters", []):
                if f["category"] == "국내지역":
                    filters.append(DomesticRegionFilter(
                        scope=f["scope"],
                        regions=f["values"]
                    ))
                elif f["category"] == "세관":
                    filters.append(CustomsOfficeFilter(
                        customs_offices=f["values"]
                    ))
            
            items_data.append(StrategyItem(
                name=item["name"],
                hs_code=item["hs_code"],
                filters=filters
            ))
        
        return cls(
            name=corp_data["name"],
            items=items_data
        )
