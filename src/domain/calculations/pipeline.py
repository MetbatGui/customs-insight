"""
Pipeline utilities for functional composition

returns 라이브러리 도입을 위한 준비 작업
현재는 간단한 pipe 함수로 시작, 향후 returns.pipeline으로 교체 예정
"""

from typing import TypeVar, Callable, List
import pandas as pd
from src.domain.models import TradeRecord, AnalysisResult
from src.domain.calculations.date_parsing import parse_period_row, format_date
from src.domain.calculations.analysis import calculate_mom_and_yoy
from src.domain.calculations.transformations import (
    dataframe_to_trade_records,
    analysis_results_to_dataframe,
    aggregate_by_date,
    sort_by_date
)


T = TypeVar('T')


def pipe(data: T, *funcs: Callable) -> T:
    """
    간단한 파이프라인 함수
    
    데이터를 여러 함수에 순차적으로 통과시킵니다.
    향후 returns.pipeline으로 교체 예정
    
    Args:
        data: 초기 데이터
        *funcs: 순차적으로 적용할 함수들
        
    Returns:
        모든 함수를 통과한 최종 결과
        
    Examples:
        >>> def add_one(x): return x + 1
        >>> def double(x): return x * 2
        >>> pipe(5, add_one, double)
        12
    """
    result = data
    for func in funcs:
        result = func(result)
    return result


def parse_and_aggregate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    원본 DataFrame을 파싱하고 날짜별로 집계
    
    순수 함수: 복잡한 로직을 재사용 가능한 파이프라인으로 조합
    
    Args:
        df: 원본 DataFrame (period_raw, export_amount 등)
        
    Returns:
        파싱 및 집계된 DataFrame (date, export_amount)
    """
    # 1. 컬럼 선택
    if df.empty:
        return pd.DataFrame(columns=['date', 'export_amount'])
    
    df_selected = df.iloc[:, [0, 1]].copy()
    df_selected.columns = ['period_raw', 'export_amount']
    
    # 2. 날짜 파싱
    processed_data = []
    current_year = None
    
    for _, row in df_selected.iterrows():
        period_val = str(row['period_raw']).strip()
        year, month = parse_period_row(period_val, current_year)
        
        if year and not month:
            # 연도 행
            current_year = year
            continue
        
        if year and month:
            # 월 행
            date_str = format_date(year, month)
            try:
                amount = float(row['export_amount'])
            except (ValueError, TypeError):
                amount = 0.0
            
            processed_data.append({
                'date': date_str,
                'export_amount': amount
            })
    
    if not processed_data:
        return pd.DataFrame(columns=['date', 'export_amount'])
    
    df_parsed = pd.DataFrame(processed_data)
    
    # 3. 파이프라인: 집계 -> 정렬
    return pipe(
        df_parsed,
        aggregate_by_date,
        sort_by_date
    )


def process_trade_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    전체 데이터 처리 파이프라인
    
    순수 함수 파이프라인으로 데이터 처리
    향후 returns의 Result, Maybe 타입으로 에러 핸들링 강화 예정
    
    Args:
        df: 원본 DataFrame
        
    Returns:
        MoM/YoY가 계산된 최종 DataFrame
        
    Examples:
        >>> # 원본 DataFrame (MultiIndex 헤더 등)
        >>> df = pd.DataFrame(...)
        >>> result = process_trade_data(df)
        >>> 'export_mom' in result.columns
        True
    """
    # 파이프라인: 
    # DataFrame -> 파싱&집계 -> TradeRecord -> MoM/YoY 계산 -> DataFrame
    
    parsed_df = parse_and_aggregate_dataframe(df)
    
    if parsed_df.empty:
        return pd.DataFrame(columns=['date', 'export_amount', 'export_mom', 'export_yoy'])
    
    # DataFrame -> TradeRecord -> AnalysisResult -> DataFrame
    return pipe(
        parsed_df,
        dataframe_to_trade_records,
        calculate_mom_and_yoy,
        analysis_results_to_dataframe
    )
