"""
Tests for date parsing pure functions

순수 함수 테스트의 특징:
- 같은 입력에 대해 항상 같은 출력 (멱등성)
- 외부 상태에 의존하지 않음
- 테스트 간 독립성
"""

import unittest
from src.domain.calculations.date_parsing import (
    parse_year,
    parse_month,
    parse_period_row,
    format_date
)


class TestParseYear(unittest.TestCase):
    """parse_year 함수 테스트"""
    
    def test_valid_year(self):
        """정상적인 연도 파싱"""
        self.assertEqual(parse_year("2024년"), "2024")
        self.assertEqual(parse_year("2023년"), "2023")
    
    def test_year_with_whitespace(self):
        """공백이 있는 연도 파싱"""
        self.assertEqual(parse_year("  2024년  "), "2024")
    
    def test_not_year(self):
        """연도가 아닌 문자열"""
        self.assertIsNone(parse_year("01월"))
        self.assertIsNone(parse_year("invalid"))
        self.assertIsNone(parse_year(""))
    
    def test_pure_function(self):
        """순수 함수: 같은 입력은 항상 같은 출력"""
        result1 = parse_year("2024년")
        result2 = parse_year("2024년")
        self.assertEqual(result1, result2)


class TestParseMonth(unittest.TestCase):
    """parse_month 함수 테스트"""
    
    def test_valid_month_with_padding(self):
        """0이 패딩된 월"""
        self.assertEqual(parse_month("01월"), "01")
        self.assertEqual(parse_month("12월"), "12")
    
    def test_valid_month_without_padding(self):
        """패딩 없는 월 (함수가 자동으로 패딩)"""
        self.assertEqual(parse_month("1월"), "01")
        self.assertEqual(parse_month("9월"), "09")
    
    def test_month_with_whitespace(self):
        """공백이 있는 월 파싱"""
        self.assertEqual(parse_month("  01월  "), "01")
    
    def test_not_month(self):
        """월이 아닌 문자열"""
        self.assertIsNone(parse_month("2024년"))
        self.assertIsNone(parse_month("invalid"))


class TestParsePeriodRow(unittest.TestCase):
    """parse_period_row 함수 테스트"""
    
    def test_year_row(self):
        """연도 행 파싱"""
        year, month = parse_period_row("2024년", None)
        self.assertEqual(year, "2024")
        self.assertIsNone(month)
    
    def test_month_row_with_year_context(self):
        """연도 컨텍스트가 있는 월 행"""
        year, month = parse_period_row("01월", "2024")
        self.assertEqual(year, "2024")
        self.assertEqual(month, "01")
    
    def test_month_row_without_year_context(self):
        """연도 컨텍스트가 없는 월 행 (무시)"""
        year, month = parse_period_row("01월", None)
        self.assertIsNone(year)
        self.assertIsNone(month)
    
    def test_invalid_row(self):
        """잘못된 형식의 행"""
        year, month = parse_period_row("invalid", "2024")
        self.assertIsNone(year)
        self.assertIsNone(month)
    
    def test_pure_function_idempotency(self):
        """순수 함수: 멱등성 검증"""
        result1 = parse_period_row("01월", "2024")
        result2 = parse_period_row("01월", "2024")
        self.assertEqual(result1, result2)


class TestFormatDate(unittest.TestCase):
    """format_date 함수 테스트"""
    
    def test_format_with_padded_month(self):
        """0이 패딩된 월"""
        self.assertEqual(format_date("2024", "01"), "2024-01")
        self.assertEqual(format_date("2024", "12"), "2024-12")
    
    def test_format_with_unpadded_month(self):
        """패딩 없는 월 (함수가 자동으로 패딩)"""
        self.assertEqual(format_date("2024", "1"), "2024-01")
        self.assertEqual(format_date("2024", "9"), "2024-09")
    
    def test_pure_function(self):
        """순수 함수: 같은 입력은 항상 같은 출력"""
        result1 = format_date("2024", "01")
        result2 = format_date("2024", "01")
        self.assertEqual(result1, result2)
        self.assertEqual(result1, "2024-01")


if __name__ == '__main__':
    unittest.main()
