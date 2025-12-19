"""
Data transformation pure functions

DataFrame ↔ Pydantic Models 변환
순수 함수: 입력 데이터를 변환하여 새로운 형태로 반환
"""

import pandas as pd
from typing import List, Dict, Any
from src.domain.models import TradeRecord, AnalysisResult


def dataframe_to_trade_records(df: pd.DataFrame) -> List[TradeRecord]:
    """
    DataFrame을 TradeRecord 리스트로 변환
    
    순수 함수: DataFrame을 불변 Pydantic 모델 리스트로 변환
    
    Args:
        df: 'date', 'export_amount' 컬럼을 가진 DataFrame
        
    Returns:
        TradeRecord 객체 리스트
        
    Raises:
        ValueError: 필수 컬럼이 없거나 데이터 형식이 잘못된 경우
        
    Examples:
        >>> df = pd.DataFrame({
        ...     'date': ['2024-01', '2024-02'],
        ...     'export_amount': [100.0, 150.0]
        ... })
        >>> records = dataframe_to_trade_records(df)
        >>> len(records)
        2
        >>> records[0].date
        '2024-01'
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
        try:
            record = TradeRecord(
                date=str(row['date']),
                export_amount=float(row['export_amount'])
            )
            records.append(record)
        except Exception as e:
            # Pydantic 검증 에러를 전파
            raise ValueError(f"Invalid data at row: {e}")
    
    return records


def analysis_results_to_dataframe(results: List[AnalysisResult]) -> pd.DataFrame:
    """
    AnalysisResult 리스트를 DataFrame으로 변환
    
    순수 함수: Pydantic 모델 리스트를 DataFrame으로 변환
    
    Args:
        results: AnalysisResult 객체 리스트
        
    Returns:
        'date', 'export_amount', 'export_mom', 'export_yoy' 컬럼을 가진 DataFrame
        
    Examples:
        >>> results = [
        ...     AnalysisResult(date="2024-01", export_amount=100.0, export_mom=None, export_yoy=None),
        ...     AnalysisResult(date="2024-02", export_amount=150.0, export_mom=50.0, export_yoy=25.0),
        ... ]
        >>> df = analysis_results_to_dataframe(results)
        >>> df.shape
        (2, 4)
        >>> list(df.columns)
        ['date', 'export_amount', 'export_mom', 'export_yoy']
    """
    if not results:
        return pd.DataFrame(columns=['date', 'export_amount', 'export_mom', 'export_yoy'])
    
    # Pydantic 모델을 딕셔너리로 변환
    data = [result.model_dump() for result in results]
    
    df = pd.DataFrame(data)
    
    # 컬럼 순서 명시적으로 설정
    df = df[['date', 'export_amount', 'export_mom', 'export_yoy']]
    
    return df


def dict_list_to_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    딕셔너리 리스트를 DataFrame으로 변환
    
    순수 함수: 중간 형태의 데이터를 DataFrame으로 변환
    
    Args:
        data: 딕셔너리 리스트
        
    Returns:
        DataFrame
        
    Examples:
        >>> data = [
        ...     {'date': '2024-01', 'export_amount': 100.0},
        ...     {'date': '2024-02', 'export_amount': 150.0}
        ... ]
        >>> df = dict_list_to_dataframe(data)
        >>> df.shape
        (2, 2)
    """
    if not data:
        return pd.DataFrame()
    
    return pd.DataFrame(data)


def aggregate_by_date(df: pd.DataFrame, value_column: str = 'export_amount') -> pd.DataFrame:
    """
    날짜별로 값을 집계 (합산)
    
    순수 함수: 같은 날짜의 여러 레코드를 하나로 합침
    
    Args:
        df: 'date'와 value_column을 포함하는 DataFrame
        value_column: 집계할 값 컬럼명
        
    Returns:
        날짜별로 집계된 DataFrame
        
    Examples:
        >>> df = pd.DataFrame({
        ...     'date': ['2024-01', '2024-01', '2024-02'],
        ...     'export_amount': [100.0, 50.0, 200.0]
        ... })
        >>> result = aggregate_by_date(df)
        >>> result.loc[result['date'] == '2024-01', 'export_amount'].values[0]
        150.0
    """
    if df.empty:
        return df
    
    if 'date' not in df.columns or value_column not in df.columns:
        raise ValueError(f"DataFrame must have 'date' and '{value_column}' columns")
    
    aggregated = df.groupby('date', as_index=False)[value_column].sum()
    
    return aggregated


def sort_by_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrame을 날짜순으로 정렬
    
    순수 함수: 입력 DataFrame을 변경하지 않고 정렬된 새 DataFrame 반환
    
    Args:
        df: 'date' 컬럼을 포함하는 DataFrame
        
    Returns:
        날짜순으로 정렬된 DataFrame (인덱스 리셋됨)
        
    Examples:
        >>> df = pd.DataFrame({
        ...     'date': ['2024-02', '2024-01'],
        ...     'export_amount': [150.0, 100.0]
        ... })
        >>> sorted_df = sort_by_date(df)
        >>> sorted_df['date'].tolist()
        ['2024-01', '2024-02']
    """
    if df.empty:
        return df
    
    if 'date' not in df.columns:
        raise ValueError("DataFrame must have 'date' column")
    
    sorted_df = df.sort_values('date').reset_index(drop=True)
    
    return sorted_df
