"""
Tests for pipeline utilities

함수형 파이프라인 테스트
"""

import unittest
import pandas as pd
from src.domain.calculations.pipeline import (
    pipe,
    parse_and_aggregate_dataframe,
    process_trade_data
)


class TestPipe(unittest.TestCase):
    """pipe 함수 테스트"""
    
    def test_single_function(self):
        """단일 함수 적용"""
        def add_one(x):
            return x + 1
        
        result = pipe(5, add_one)
        self.assertEqual(result, 6)
    
    def test_multiple_functions(self):
        """여러 함수 순차 적용"""
        def add_one(x):
            return x + 1
        
        def double(x):
            return x * 2
        
        def subtract_three(x):
            return x - 3
        
        result = pipe(5, add_one, double, subtract_three)
        # (5 + 1) * 2 - 3 = 9
        self.assertEqual(result, 9)
    
    def test_no_functions(self):
        """함수 없이 호출 (데이터 그대로 반환)"""
        result = pipe(10)
        self.assertEqual(result, 10)
    
    def test_pure_function_composition(self):
        """순수 함수 조합: 멱등성"""
        def times_two(x):
            return x * 2
        
        result1 = pipe(5, times_two, times_two)
        result2 = pipe(5, times_two, times_two)
        
        self.assertEqual(result1, result2)
        self.assertEqual(result1, 20)


class TestParseAndAggregateDataframe(unittest.TestCase):
    """parse_and_aggregate_dataframe 함수 테스트"""
    
    def test_basic_parsing(self):
        """기본 파싱 및 집계"""
        df = pd.DataFrame({
            'period': ['2024년', '01월', '02월'],
            'amount': [None, 100.0, 150.0]
        })
        
        result = parse_and_aggregate_dataframe(df)
        
        self.assertEqual(len(result), 2)
        self.assertIn('date', result.columns)
        self.assertIn('export_amount', result.columns)
        self.assertEqual(result.iloc[0]['date'], '2024-01')
        self.assertEqual(result.iloc[0]['export_amount'], 100.0)
    
    def test_aggregation_of_duplicates(self):
        """중복 날짜 집계"""
        df = pd.DataFrame({
            'period': ['2024년', '01월', '01월', '02월'],
            'amount': [None, 50.0, 50.0, 100.0]
        })
        
        result = parse_and_aggregate_dataframe(df)
        
        self.assertEqual(len(result), 2)
        jan_amount = result.loc[result['date'] == '2024-01', 'export_amount'].values[0]
        self.assertEqual(jan_amount, 100.0)
    
    def test_empty_dataframe(self):
        """빈 DataFrame"""
        df = pd.DataFrame()
        result = parse_and_aggregate_dataframe(df)
        
        self.assertTrue(result.empty)
        self.assertListEqual(list(result.columns), ['date', 'export_amount'])


class TestProcessTradeData(unittest.TestCase):
    """process_trade_data 전체 파이프라인 테스트"""
    
    def test_end_to_end_pipeline(self):
        """전체 파이프라인: DataFrame -> MoM/YoY 계산"""
        df = pd.DataFrame({
            'period': ['2023년', '01월', '02월', '2024년', '01월'],
            'amount': [None, 100.0, 110.0, None, 150.0]
        })
        
        result = process_trade_data(df)
        
        # 결과 검증
        self.assertEqual(len(result), 3)
        self.assertListEqual(
            list(result.columns),
            ['date', 'export_amount', 'export_mom', 'export_yoy']
        )
        
        # 2023-01: 첫 레코드
        self.assertEqual(result.iloc[0]['date'], '2023-01')
        self.assertTrue(pd.isna(result.iloc[0]['export_mom']))
        
        # 2023-02: MoM 계산됨
        self.assertEqual(result.iloc[1]['date'], '2023-02')
        self.assertEqual(result.iloc[1]['export_mom'], 10.0)
        
        # 2024-01: MoM과 YoY 모두 계산됨
        self.assertEqual(result.iloc[2]['date'], '2024-01')
        self.assertIsNotNone(result.iloc[2]['export_mom'])
        self.assertEqual(result.iloc[2]['export_yoy'], 50.0)
    
    def test_empty_input(self):
        """빈 입력"""
        df = pd.DataFrame()
        result = process_trade_data(df)
        
        self.assertTrue(result.empty)
        self.assertListEqual(
            list(result.columns),
            ['date', 'export_amount', 'export_mom', 'export_yoy']
        )
    
    def test_sorted_output(self):
        """출력이 날짜순으로 정렬되는지 확인"""
        df = pd.DataFrame({
            'period': ['2024년', '03월', '01월', '02월'],
            'amount': [None, 300.0, 100.0, 200.0]
        })
        
        result = process_trade_data(df)
        
        dates = result['date'].tolist()
        self.assertEqual(dates, sorted(dates))


if __name__ == '__main__':
    unittest.main()
