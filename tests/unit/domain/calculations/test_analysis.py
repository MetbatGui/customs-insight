"""
Tests for analysis calculation pure functions (MoM, YoY)

순수 함수 테스트:
- 불변 입력에 대한 일관된 출력
- Pydantic 모델 사용
- 경계 조건 테스트
"""

import unittest
from src.domain.models import TradeRecord, AnalysisResult
from src.domain.calculations.analysis import (
    calculate_percentage_change,
    calculate_mom,
    calculate_yoy,
    calculate_mom_and_yoy
)


class TestCalculatePercentageChange(unittest.TestCase):
    """calculate_percentage_change 함수 테스트"""
    
    def test_positive_change(self):
        """양수 증가"""
        result = calculate_percentage_change(150, 100)
        self.assertEqual(result, 50.0)
    
    def test_negative_change(self):
        """음수 감소"""
        result = calculate_percentage_change(80, 100)
        self.assertEqual(result, -20.0)
    
    def test_no_change(self):
        """변화 없음"""
        result = calculate_percentage_change(100, 100)
        self.assertEqual(result, 0.0)
    
    def test_division_by_zero(self):
        """0으로 나누기 (이전 값이 0)"""
        result = calculate_percentage_change(100, 0)
        self.assertIsNone(result)
    
    def test_rounding(self):
        """소수점 2자리 반올림"""
        result = calculate_percentage_change(100, 3)
        self.assertEqual(result, 3233.33)


class TestCalculateMom(unittest.TestCase):
    """calculate_mom 함수 테스트"""
    
    def test_empty_list(self):
        """빈 리스트"""
        result = calculate_mom([])
        self.assertEqual(result, [])
    
    def test_single_record(self):
        """단일 레코드: MoM은 None"""
        records = [TradeRecord(date="2024-01", export_amount=100.0)]
        results = calculate_mom(records)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].date, "2024-01")
        self.assertEqual(results[0].export_amount, 100.0)
        self.assertIsNone(results[0].export_mom)
        self.assertIsNone(results[0].export_yoy)
    
    def test_two_records(self):
        """두 레코드: 두 번째의 MoM 계산"""
        records = [
            TradeRecord(date="2024-01", export_amount=100.0),
            TradeRecord(date="2024-02", export_amount=150.0),
        ]
        results = calculate_mom(records)
        
        self.assertEqual(len(results), 2)
        self.assertIsNone(results[0].export_mom)
        self.assertEqual(results[1].export_mom, 50.0)
    
    def test_multiple_records(self):
        """여러 레코드"""
        records = [
            TradeRecord(date="2024-01", export_amount=100.0),
            TradeRecord(date="2024-02", export_amount=110.0),
            TradeRecord(date="2024-03", export_amount=121.0),
        ]
        results = calculate_mom(records)
        
        self.assertEqual(len(results), 3)
        self.assertIsNone(results[0].export_mom)
        self.assertEqual(results[1].export_mom, 10.0)
        self.assertEqual(results[2].export_mom, 10.0)
    
    def test_pure_function_idempotency(self):
        """순수 함수: 같은 입력은 항상 같은 출력"""
        records = [
            TradeRecord(date="2024-01", export_amount=100.0),
            TradeRecord(date="2024-02", export_amount=150.0),
        ]
        
        result1 = calculate_mom(records)
        result2 = calculate_mom(records)
        
        self.assertEqual(result1, result2)


class TestCalculateYoY(unittest.TestCase):
    """calculate_yoy 함수 테스트"""
    
    def test_empty_list(self):
        """빈 리스트"""
        result = calculate_yoy([])
        self.assertEqual(result, [])
    
    def test_no_previous_year_data(self):
        """전년 데이터 없음: YoY는 None"""
        records = [
            AnalysisResult(date="2024-01", export_amount=100.0, export_mom=None, export_yoy=None)
        ]
        results = calculate_yoy(records)
        
        self.assertEqual(len(results), 1)
        self.assertIsNone(results[0].export_yoy)
    
    def test_with_previous_year_data(self):
        """전년 데이터 있음: YoY 계산"""
        records = [
            AnalysisResult(date="2023-01", export_amount=100.0, export_mom=None, export_yoy=None),
            AnalysisResult(date="2024-01", export_amount=150.0, export_mom=50.0, export_yoy=None),
        ]
        results = calculate_yoy(records)
        
        self.assertEqual(len(results), 2)
        self.assertIsNone(results[0].export_yoy)
        self.assertEqual(results[1].export_yoy, 50.0)
    
    def test_multiple_years(self):
        """여러 연도 데이터"""
        records = [
            AnalysisResult(date="2022-01", export_amount=80.0, export_mom=None, export_yoy=None),
            AnalysisResult(date="2023-01", export_amount=100.0, export_mom=25.0, export_yoy=None),
            AnalysisResult(date="2024-01", export_amount=150.0, export_mom=50.0, export_yoy=None),
        ]
        results = calculate_yoy(records)
        
        self.assertEqual(len(results), 3)
        self.assertIsNone(results[0].export_yoy)
        self.assertEqual(results[1].export_yoy, 25.0)  # (100-80)/80 = 25%
        self.assertEqual(results[2].export_yoy, 50.0)  # (150-100)/100 = 50%
    
    def test_preserves_mom_values(self):
        """MoM 값이 보존됨"""
        records = [
            AnalysisResult(date="2023-01", export_amount=100.0, export_mom=None, export_yoy=None),
            AnalysisResult(date="2024-01", export_amount=150.0, export_mom=99.99, export_yoy=None),
        ]
        results = calculate_yoy(records)
        
        self.assertEqual(results[1].export_mom, 99.99)  # MoM 값 유지
        self.assertEqual(results[1].export_yoy, 50.0)   # YoY 계산


class TestCalculateMomAndYoY(unittest.TestCase):
    """calculate_mom_and_yoy 통합 함수 테스트"""
    
    def test_full_pipeline(self):
        """전체 파이프라인: TradeRecord -> AnalysisResult"""
        records = [
            TradeRecord(date="2023-01", export_amount=100.0),
            TradeRecord(date="2023-02", export_amount=110.0),
            TradeRecord(date="2024-01", export_amount=150.0),
            TradeRecord(date="2024-02", export_amount=165.0),
        ]
        results = calculate_mom_and_yoy(records)
        
        self.assertEqual(len(results), 4)
        
        # 2023-01: 첫 레코드
        self.assertIsNone(results[0].export_mom)
        self.assertIsNone(results[0].export_yoy)
        
        # 2023-02: MoM만 계산
        self.assertEqual(results[1].export_mom, 10.0)
        self.assertIsNone(results[1].export_yoy)
        
        # 2024-01: MoM과 YoY 모두 계산
        self.assertEqual(results[2].export_mom, 36.36)  # (150-110)/110
        self.assertEqual(results[2].export_yoy, 50.0)   # (150-100)/100
        
        # 2024-02: MoM과 YoY 모두 계산
        self.assertEqual(results[3].export_mom, 10.0)   # (165-150)/150
        self.assertEqual(results[3].export_yoy, 50.0)   # (165-110)/110
    
    def test_empty_input(self):
        """빈 입력"""
        results = calculate_mom_and_yoy([])
        self.assertEqual(results, [])


if __name__ == '__main__':
    unittest.main()
