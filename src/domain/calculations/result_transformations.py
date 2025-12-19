"""
Result-based transformations using returns library

returns 라이브러리를 활용한 안전한 데이터 변환
Result 타입으로 에러 핸들링 개선
"""

import pandas as pd
from typing import List
from returns.result import Result, Success, Failure, safe
from src.domain.models import TradeRecord, AnalysisResult


@safe
def dataframe_to_trade_records_safe(df: pd.DataFrame) -> List[TradeRecord]:
    """
    DataFrame을 TradeRecord 리스트로 안전하게 변환
    
    Result 타입 사용: 성공/실패를 명시적으로 처리
    
    Args:
        df: 'date', 'export_amount' 컬럼을 가진 DataFrame
        
    Returns:
        Result[List[TradeRecord], Exception]
        - Success: TradeRecord 리스트
        - Failure: 변환 중 발생한 에러
        
    Examples:
        >>> df = pd.DataFrame({
        ...     'date': ['2024-01'],
        ...     'export_amount': [100.0]
        ... })
        >>> result = dataframe_to_trade_records_safe(df)
        >>> isinstance(result, Success)
        True
    """
    if df.empty:
        return []
    
    # 필수 컬럼 확인
    required_columns = {'date', 'export_amount'}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"Missing required columns: {missing}")
    
    records = []
    for _, row in df.iterrows():
        # Pydantic 검증이 자동으로 실행됨
        record = TradeRecord(
            date=str(row['date']),
            export_amount=float(row['export_amount'])
        )
        records.append(record)
    
    return records


def process_trade_data_safe(df: pd.DataFrame) -> Result[pd.DataFrame, str]:
    """
    Result 타입을 사용한 안전한 데이터 처리
    
    에러가 발생하면 Failure를 반환하여 명시적으로 처리
    
    Args:
        df: 원본 DataFrame
        
    Returns:
        Result[pd.DataFrame, str]
        - Success: 처리된 DataFrame
        - Failure: 에러 메시지
        
    Examples:
        >>> df = pd.DataFrame(...)
        >>> result = process_trade_data_safe(df)
        >>> result.map(lambda d: d.shape)  # Success인 경우에만 실행
    """
    from src.domain.calculations.pipeline import parse_and_aggregate_dataframe
    from src.domain.calculations.analysis import calculate_mom_and_yoy
    from src.domain.calculations.transformations import analysis_results_to_dataframe
    
    try:
        # 1단계: 파싱 및 집계
        parsed_df = parse_and_aggregate_dataframe(df)
        
        if parsed_df.empty:
            return Success(pd.DataFrame(
                columns=['date', 'export_amount', 'export_mom', 'export_yoy']
            ))
        
        # 2단계: Result 타입으로 변환 시도
        records_result = dataframe_to_trade_records_safe(parsed_df)
        
        # Result를 unwrap하거나 에러 처리
        if isinstance(records_result, Failure):
            return Failure(f"Failed to convert to TradeRecord: {records_result.failure()}")
        
        records = records_result.unwrap()
        
        # 3단계: MoM/YoY 계산
        analysis_results = calculate_mom_and_yoy(records)
        
        # 4단계: DataFrame으로 변환
        result_df = analysis_results_to_dataframe(analysis_results)
        
        return Success(result_df)
        
    except Exception as e:
        return Failure(f"Error processing trade data: {str(e)}")


def safe_aggregate_by_date(df: pd.DataFrame) -> Result[pd.DataFrame, str]:
    """
    Result 타입을 사용한 안전한 집계
    
    Args:
        df: 집계할 DataFrame
        
    Returns:
        Result[pd.DataFrame, str]
    """
    try:
        if df.empty:
            return Success(df)
        
        if 'date' not in df.columns or 'export_amount' not in df.columns:
            return Failure("Missing required columns: date or export_amount")
        
        aggregated = df.groupby('date', as_index=False)['export_amount'].sum()
        return Success(aggregated)
        
    except Exception as e:
        return Failure(f"Aggregation failed: {str(e)}")
