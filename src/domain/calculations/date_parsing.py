"""
Date parsing pure functions

순수 함수들:
- 외부 상태에 의존하지 않음
- 같은 입력에 대해 항상 같은 출력
- 부수 효과 없음
"""

import re
from typing import Optional, Tuple


def parse_year(period_str: str) -> Optional[str]:
    """
    연도 문자열 파싱 (예: "2024년" -> "2024")
    
    Args:
        period_str: 파싱할 기간 문자열
        
    Returns:
        파싱된 연도 문자열, 연도가 아니면 None
        
    Examples:
        >>> parse_year("2024년")
        '2024'
        >>> parse_year("01월")
        None
    """
    year_match = re.match(r'(\d{4})년', period_str.strip())
    if year_match:
        return year_match.group(1)
    return None


def parse_month(period_str: str) -> Optional[str]:
    """
    월 문자열 파싱 (예: "01월" -> "01", "1월" -> "01")
    
    Args:
        period_str: 파싱할 기간 문자열
        
    Returns:
        파싱된 월 문자열 (2자리, 0 패딩), 월이 아니면 None
        
    Examples:
        >>> parse_month("01월")
        '01'
        >>> parse_month("1월")
        '01'
        >>> parse_month("2024년")
        None
    """
    month_match = re.match(r'(\d{1,2})월', period_str.strip())
    if month_match:
        return month_match.group(1).zfill(2)
    return None


def parse_period_row(period_str: str, current_year: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    기간 문자열을 파싱하여 (year, month) 반환
    
    순수 함수: 외부 상태 없이 입력만으로 출력 결정
    
    Args:
        period_str: 파싱할 기간 문자열
        current_year: 현재 처리 중인 연도 (컨텍스트)
        
    Returns:
        (year, month) 튜플. 각 값은 파싱되었으면 문자열, 아니면 None
        - 연도 행: (year, None)
        - 월 행 (연도 있을 때): (current_year, month)
        - 월 행 (연도 없을 때): (None, None)
        - 기타: (None, None)
        
    Examples:
        >>> parse_period_row("2024년", None)
        ('2024', None)
        >>> parse_period_row("01월", "2024")
        ('2024', '01')
        >>> parse_period_row("01월", None)
        (None, None)
    """
    period_str = period_str.strip()
    
    # 연도 체크
    year = parse_year(period_str)
    if year:
        return (year, None)
    
    # 월 체크
    month = parse_month(period_str)
    if month and current_year:
        return (current_year, month)
    
    return (None, None)


def format_date(year: str, month: str) -> str:
    """
    연도와 월을 YYYY-MM 형식으로 포맷
    
    Args:
        year: 연도 문자열 (4자리)
        month: 월 문자열 (1-2자리, 함수 내에서 0 패딩)
        
    Returns:
        YYYY-MM 형식의 날짜 문자열
        
    Examples:
        >>> format_date("2024", "01")
        '2024-01'
        >>> format_date("2024", "1")
        '2024-01'
    """
    return f"{year}-{month.zfill(2)}"
