"""
Analysis calculation pure functions (MoM, YoY)

순수 함수들:
- List[TradeRecord] -> List[AnalysisResult] 변환
- 불변 데이터 사용 (Pydantic 모델)
- 부수 효과 없음
"""

from typing import List, Optional
from src.domain.models import TradeRecord, AnalysisResult


def calculate_percentage_change(current: float, previous: float) -> Optional[float]:
    """
    두 값 사이의 증감률 계산
    
    Args:
        current: 현재 값
        previous: 이전 값
        
    Returns:
        증감률 (%), 이전 값이 0이면 None
        
    Examples:
        >>> calculate_percentage_change(150, 100)
        50.0
        >>> calculate_percentage_change(80, 100)
        -20.0
        >>> calculate_percentage_change(100, 0)
        None
    """
    if previous == 0:
        return None
    return round(((current - previous) / previous) * 100, 2)


def calculate_mom(records: List[TradeRecord]) -> List[AnalysisResult]:
    """
    MoM (Month over Month) 계산
    
    순수 함수: 정렬된 TradeRecord 리스트를 받아 MoM이 포함된 AnalysisResult 리스트 반환
    
    Args:
        records: 날짜순으로 정렬된 TradeRecord 리스트
        
    Returns:
        MoM이 계산된 AnalysisResult 리스트
        첫 번째 레코드의 MoM은 None (비교 대상 없음)
        
    Examples:
        >>> records = [
        ...     TradeRecord(date="2024-01", export_amount=100.0),
        ...     TradeRecord(date="2024-02", export_amount=150.0),
        ... ]
        >>> results = calculate_mom(records)
        >>> results[0].export_mom is None
        True
        >>> results[1].export_mom
        50.0
    """
    if not records:
        return []
    
    results = []
    for i, record in enumerate(records):
        if i == 0:
            # 첫 레코드는 비교 대상 없음
            mom = None
        else:
            prev_amount = records[i - 1].export_amount
            mom = calculate_percentage_change(record.export_amount, prev_amount)
        
        results.append(AnalysisResult(
            date=record.date,
            export_amount=record.export_amount,
            export_mom=mom,
            export_yoy=None  # YoY는 별도 함수에서 계산
        ))
    
    return results


def calculate_yoy(records: List[AnalysisResult]) -> List[AnalysisResult]:
    """
    YoY (Year over Year) 계산
    
    순수 함수: AnalysisResult 리스트를 받아 YoY를 추가하여 반환
    
    Args:
        records: MoM이 계산된 AnalysisResult 리스트 (날짜순 정렬 가정)
        
    Returns:
        YoY가 추가된 새로운 AnalysisResult 리스트
        12개월 전 데이터가 없으면 YoY는 None
        
    Examples:
        >>> records = [
        ...     AnalysisResult(date="2023-01", export_amount=100.0, export_mom=None, export_yoy=None),
        ...     AnalysisResult(date="2024-01", export_amount=150.0, export_mom=50.0, export_yoy=None),
        ... ]
        >>> results = calculate_yoy(records)
        >>> results[0].export_yoy is None
        True
        >>> results[1].export_yoy
        50.0
    """
    if not records:
        return []
    
    # 날짜를 키로 하는 lookup 딕셔너리 생성
    amount_by_date = {r.date: r.export_amount for r in records}
    
    results = []
    for record in records:
        # 12개월 전 날짜 계산 (YYYY-MM 형식)
        year, month = record.date.split('-')
        prev_year = str(int(year) - 1)
        prev_date = f"{prev_year}-{month}"
        
        # 전년 동월 데이터가 있으면 YoY 계산
        if prev_date in amount_by_date:
            prev_amount = amount_by_date[prev_date]
            yoy = calculate_percentage_change(record.export_amount, prev_amount)
        else:
            yoy = None
        
        # 새 AnalysisResult 생성 (불변 객체이므로 복사 필요)
        results.append(AnalysisResult(
            date=record.date,
            export_amount=record.export_amount,
            export_mom=record.export_mom,
            export_yoy=yoy
        ))
    
    return results


def calculate_mom_and_yoy(records: List[TradeRecord]) -> List[AnalysisResult]:
    """
    MoM과 YoY를 모두 계산하는 헬퍼 함수
    
    순수 함수: TradeRecord 리스트를 받아 MoM/YoY가 계산된 AnalysisResult 반환
    
    Args:
        records: 날짜순으로 정렬된 TradeRecord 리스트
        
    Returns:
        MoM과 YoY가 모두 계산된 AnalysisResult 리스트
        
    Examples:
        >>> records = [
        ...     TradeRecord(date="2023-01", export_amount=100.0),
        ...     TradeRecord(date="2023-02", export_amount=110.0),
        ...     TradeRecord(date="2024-01", export_amount=150.0),
        ... ]
        >>> results = calculate_mom_and_yoy(records)
        >>> len(results)
        3
        >>> results[2].export_mom  # 2024-01의 MoM (vs 2023-02)
        36.36
        >>> results[2].export_yoy  # 2024-01의 YoY (vs 2023-01)
        50.0
    """
    # 파이프라인: TradeRecord -> (MoM 추가) -> (YoY 추가) -> AnalysisResult
    with_mom = calculate_mom(records)
    with_yoy = calculate_yoy(with_mom)
    return with_yoy
