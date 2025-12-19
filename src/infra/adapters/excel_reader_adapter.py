"""
Safe Excel reading functions using returns library

Result 타입으로 안전한 Excel 파일 읽기
"""

import pandas as pd
from pathlib import Path
from returns.result import Result, Success, Failure, safe
from typing import List, Any


@safe
def _read_excel_file(file_path: str, header: List[int] | int | None = None) -> pd.DataFrame:
    """
    Excel 파일을 읽는 순수 함수
    
    @safe 데코레이터로 자동 Exception → Failure 변환
    
    Args:
        file_path: Excel 파일 경로
        header: 헤더 행 번호 (None, int, 또는 list)
        
    Returns:
        DataFrame
        
    Raises:
        Exception: Excel 읽기 실패 시 (@safe가 Failure로 변환)
    """
    return pd.read_excel(file_path, header=header)


def read_excel_safe(
    file_path: str,
    header: List[int] | int | None = [2, 3]
) -> Result[pd.DataFrame, str]:
    """
    Result 타입으로 안전한 Excel 파일 읽기
    
    파일이 없거나 읽기에 실패하면 Failure 반환
    성공하면 Success[DataFrame] 반환
    
    Args:
        file_path: Excel 파일 경로
        header: 헤더 행 번호 (기본값: [2, 3] for MultiIndex)
        
    Returns:
        Result[pd.DataFrame, str]
        - Success: DataFrame
        - Failure: 에러 메시지
        
    Examples:
        >>> result = read_excel_safe("data.xlsx")
        >>> result.map(lambda df: df.shape)  # Success인 경우에만 실행
        Success((10, 5))
        
        >>> result = read_excel_safe("missing.xlsx")
        >>> isinstance(result, Failure)
        True
    """
    path = Path(file_path)
    
    # 1단계: 파일 존재 확인
    if not path.exists():
        return Failure(f"File not found: {file_path}")
    
    # 2단계: Excel 읽기 (@safe가 Exception → Failure 변환)
    return (
        _read_excel_file(file_path, header=header)
        .alt(lambda e: f"Error reading Excel file: {str(e)}")
    )


def read_excel_with_fallback(
    file_path: str,
    primary_header: List[int] | int | None = [2, 3],
    fallback_header: List[int] | int | None = None
) -> Result[pd.DataFrame, str]:
    """
    헤더 읽기 실패 시 fallback 헤더로 재시도
    
    Args:
        file_path: Excel 파일 경로
        primary_header: 기본 헤더 설정
        fallback_header: 실패 시 사용할 헤더 설정
        
    Returns:
        Result[pd.DataFrame, str]
    """
    result = read_excel_safe(file_path, header=primary_header)
    
    # 실패이고 fallback이 있으면 재시도
    if isinstance(result, Failure) and fallback_header is not None:
        return read_excel_safe(file_path, header=fallback_header)
    
    return result


# 기존 클래스와의 호환성을 위한 래퍼
class ExcelReaderAdapter:
    """
    하위 호환성을 위한 래퍼 클래스
    
    내부적으로는 Result 타입 함수를 사용하지만,
    기존 인터페이스(Exception raise)를 유지합니다.
    """
    
    def read(self, file_path: str) -> pd.DataFrame:
        """
        Excel 파일 읽기 (기존 인터페이스)
        
        Args:
            file_path: Excel 파일 경로
            
        Returns:
            DataFrame
            
        Raises:
            FileNotFoundError: 파일이 없는 경우
            Exception: Excel 읽기 실패
        """
        result = read_excel_safe(file_path, header=[2, 3])
        
        # Result → Exception 변환 (기존 코드 호환)
        if isinstance(result, Success):
            return result.unwrap()
        else:
            error_msg = result.failure()
            if "File not found" in error_msg:
                raise FileNotFoundError(error_msg)
            else:
                raise Exception(error_msg)
    
    def read_safe(self, file_path: str) -> Result[pd.DataFrame, str]:
        """
        Result 타입으로 안전한 읽기 (새로운 인터페이스)
        
        Args:
            file_path: Excel 파일 경로
            
        Returns:
            Result[pd.DataFrame, str]
        """
        return read_excel_safe(file_path, header=[2, 3])