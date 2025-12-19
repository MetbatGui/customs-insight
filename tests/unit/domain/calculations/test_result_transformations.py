"""
Tests for Result-based transformations

returns 라이브러리의 Result 타입 테스트
"""

import unittest
import pandas as pd
from returns.result import Success, Failure
from src.domain.calculations.result_transformations import (
    dataframe_to_trade_records_safe,
    process_trade_data_safe,
    safe_aggregate_by_date
)


class TestDataframeToTradeRecordsSafe(unittest.TestCase):
    """dataframe_to_trade_records_safe 함수 테스트"""
    
    def test_success_case(self):
        """정상적인 변환 - Success 반환"""
        df = pd.DataFrame({
            'date': ['2024-01', '2024-02'],
            'export_amount': [100.0, 150.0]
        })
        
        result = dataframe_to_trade_records_safe(df)
        
        self.assertIsInstance(result, Success)
        records = result.unwrap()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].date, '2024-01')
    
    def test_empty_dataframe(self):
        """빈 DataFrame - Success with empty list"""
        df = pd.DataFrame(columns=['date', 'export_amount'])
        
        result = dataframe_to_trade_records_safe(df)
        
        self.assertIsInstance(result, Success)
        self.assertEqual(result.unwrap(), [])
    
    def test_missing_columns(self):
        """필수 컬럼 누락 - Failure 반환"""
        df = pd.DataFrame({'date': ['2024-01']})
        
        result = dataframe_to_trade_records_safe(df)
        
        self.assertIsInstance(result, Failure)
    
    def test_invalid_data_format(self):
        """잘못된 데이터 형식 - Failure 반환"""
        df = pd.DataFrame({
            'date': ['invalid-date'],  # 잘못된 형식
            'export_amount': [100.0]
        })
        
        result = dataframe_to_trade_records_safe(df)
        
        self.assertIsInstance(result, Failure)


class TestProcessTradeDataSafe(unittest.TestCase):
    """process_trade_data_safe 함수 테스트"""
    
    def test_success_pipeline(self):
        """정상적인 파이프라인 - Success 반환"""
        df = pd.DataFrame({
            'period': ['2024년', '01월', '02월'],
            'amount': [None, 100.0, 150.0]
        })
        
        result = process_trade_data_safe(df)
        
        self.assertIsInstance(result, Success)
        result_df = result.unwrap()
        self.assertIn('export_mom', result_df.columns)
        self.assertIn('export_yoy', result_df.columns)
    
    def test_empty_input(self):
        """빈 입력 - Success with empty DataFrame"""
        df = pd.DataFrame()
        
        result = process_trade_data_safe(df)
        
        self.assertIsInstance(result, Success)
        result_df = result.unwrap()
        self.assertTrue(result_df.empty)
    
    def test_result_mapping(self):
        """Result.map() 함수형 처리 테스트"""
        df = pd.DataFrame({
            'period': ['2024년', '01월'],
            'amount': [None, 100.0]
        })
        
        result = process_trade_data_safe(df)
        
        # map으로 Success 값만 변환
        row_count = result.map(lambda d: len(d))
        
        self.assertIsInstance(row_count, Success)
        self.assertEqual(row_count.unwrap(), 1)
    
    def test_result_bind_chaining(self):
        """Result.bind()로 함수 체이닝"""
        df = pd.DataFrame({
            'period': ['2024년', '01월', '02월'],
            'amount': [None, 100.0, 150.0]
        })
        
        # bind로 연속적인 변환
        result = (
            process_trade_data_safe(df)
            .map(lambda d: d[['date', 'export_amount']])  # 컬럼 선택
            .map(lambda d: len(d))  # 행 개수
        )
        
        self.assertIsInstance(result, Success)
        self.assertEqual(result.unwrap(), 2)


class TestSafeAggregateByDate(unittest.TestCase):
    """safe_aggregate_by_date 함수 테스트"""
    
    def test_success_aggregation(self):
        """정상적인 집계 - Success 반환"""
        df = pd.DataFrame({
            'date': ['2024-01', '2024-01', '2024-02'],
            'export_amount': [50.0, 50.0, 100.0]
        })
        
        result = safe_aggregate_by_date(df)
        
        self.assertIsInstance(result, Success)
        aggregated = result.unwrap()
        self.assertEqual(len(aggregated), 2)
    
    def test_missing_columns_failure(self):
        """필수 컬럼 누락 - Failure 반환"""
        df = pd.DataFrame({'date': ['2024-01']})
        
        result = safe_aggregate_by_date(df)
        
        self.assertIsInstance(result, Failure)
        error_msg = result.failure()
        self.assertIn('Missing required columns', error_msg)
    
    def test_empty_dataframe(self):
        """빈 DataFrame - Success 반환"""
        df = pd.DataFrame(columns=['date', 'export_amount'])
        
        result = safe_aggregate_by_date(df)
        
        self.assertIsInstance(result, Success)


if __name__ == '__main__':
    unittest.main()
