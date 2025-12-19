"""
Tests for data transformation pure functions

DataFrame ↔ Pydantic Models 변환 테스트
"""

import unittest
import pandas as pd
from src.domain.models import TradeRecord, AnalysisResult
from src.domain.calculations.transformations import (
    dataframe_to_trade_records,
    analysis_results_to_dataframe,
    dict_list_to_dataframe,
    aggregate_by_date,
    sort_by_date
)


class TestDataframeToTradeRecords(unittest.TestCase):
    """dataframe_to_trade_records 함수 테스트"""
    
    def test_valid_dataframe(self):
        """정상적인 DataFrame 변환"""
        df = pd.DataFrame({
            'date': ['2024-01', '2024-02'],
            'export_amount': [100.0, 150.0]
        })
        
        records = dataframe_to_trade_records(df)
        
        self.assertEqual(len(records), 2)
        self.assertIsInstance(records[0], TradeRecord)
        self.assertEqual(records[0].date, '2024-01')
        self.assertEqual(records[0].export_amount, 100.0)
    
    def test_empty_dataframe(self):
        """빈 DataFrame"""
        df = pd.DataFrame(columns=['date', 'export_amount'])
        records = dataframe_to_trade_records(df)
        self.assertEqual(records, [])
    
    def test_missing_columns(self):
        """필수 컬럼 누락"""
        df = pd.DataFrame({'date': ['2024-01']})
        
        with self.assertRaises(ValueError) as context:
            dataframe_to_trade_records(df)
        
        self.assertIn('Missing required columns', str(context.exception))
    
    def test_invalid_data_format(self):
        """잘못된 데이터 형식 (Pydantic 검증 실패)"""
        df = pd.DataFrame({
            'date': ['invalid-date'],  # 잘못된 날짜 형식
            'export_amount': [100.0]
        })
        
        with self.assertRaises(ValueError):
            dataframe_to_trade_records(df)


class TestAnalysisResultsToDataframe(unittest.TestCase):
    """analysis_results_to_dataframe 함수 테스트"""
    
    def test_valid_results(self):
        """정상적인 AnalysisResult 리스트 변환"""
        results = [
            AnalysisResult(date="2024-01", export_amount=100.0, export_mom=None, export_yoy=None),
            AnalysisResult(date="2024-02", export_amount=150.0, export_mom=50.0, export_yoy=25.0),
        ]
        
        df = analysis_results_to_dataframe(results)
        
        self.assertEqual(df.shape, (2, 4))
        self.assertListEqual(list(df.columns), ['date', 'export_amount', 'export_mom', 'export_yoy'])
        self.assertEqual(df.iloc[0]['date'], '2024-01')
        self.assertEqual(df.iloc[1]['export_mom'], 50.0)
    
    def test_empty_list(self):
        """빈 리스트"""
        df = analysis_results_to_dataframe([])
        
        self.assertTrue(df.empty)
        self.assertListEqual(list(df.columns), ['date', 'export_amount', 'export_mom', 'export_yoy'])
    
    def test_none_values(self):
        """None 값 처리"""
        results = [
            AnalysisResult(date="2024-01", export_amount=100.0, export_mom=None, export_yoy=None),
        ]
        
        df = analysis_results_to_dataframe(results)
        
        self.assertTrue(pd.isna(df.iloc[0]['export_mom']))
        self.assertTrue(pd.isna(df.iloc[0]['export_yoy']))


class TestDictListToDataframe(unittest.TestCase):
    """dict_list_to_dataframe 함수 테스트"""
    
    def test_valid_dict_list(self):
        """정상적인 딕셔너리 리스트 변환"""
        data = [
            {'date': '2024-01', 'export_amount': 100.0},
            {'date': '2024-02', 'export_amount': 150.0}
        ]
        
        df = dict_list_to_dataframe(data)
        
        self.assertEqual(df.shape, (2, 2)        )
        self.assertEqual(df.iloc[0]['date'], '2024-01')
    
    def test_empty_list(self):
        """빈 리스트"""
        df = dict_list_to_dataframe([])
        self.assertTrue(df.empty)


class TestAggregateByDate(unittest.TestCase):
    """aggregate_by_date 함수 테스트"""
    
    def test_aggregate_duplicates(self):
        """중복 날짜 집계"""
        df = pd.DataFrame({
            'date': ['2024-01', '2024-01', '2024-02'],
            'export_amount': [100.0, 50.0, 200.0]
        })
        
        result = aggregate_by_date(df)
        
        self.assertEqual(len(result), 2)
        jan_amount = result.loc[result['date'] == '2024-01', 'export_amount'].values[0]
        self.assertEqual(jan_amount, 150.0)
    
    def test_no_duplicates(self):
        """중복 없는 경우"""
        df = pd.DataFrame({
            'date': ['2024-01', '2024-02'],
            'export_amount': [100.0, 200.0]
        })
        
        result = aggregate_by_date(df)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[0]['export_amount'], 100.0)
    
    def test_empty_dataframe(self):
        """빈 DataFrame"""
        df = pd.DataFrame(columns=['date', 'export_amount'])
        result = aggregate_by_date(df)
        self.assertTrue(result.empty)
    
    def test_missing_columns(self):
        """필수 컬럼 누락"""
        df = pd.DataFrame({'date': ['2024-01']})
        
        with self.assertRaises(ValueError):
            aggregate_by_date(df)


class TestSortByDate(unittest.TestCase):
    """sort_by_date 함수 테스트"""
    
    def test_sort_unsorted_data(self):
        """정렬되지 않은 데이터 정렬"""
        df = pd.DataFrame({
            'date': ['2024-03', '2024-01', '2024-02'],
            'export_amount': [300.0, 100.0, 200.0]
        })
        
        sorted_df = sort_by_date(df)
        
        self.assertListEqual(sorted_df['date'].tolist(), ['2024-01', '2024-02', '2024-03'])
    
    def test_already_sorted(self):
        """이미 정렬된 데이터"""
        df = pd.DataFrame({
            'date': ['2024-01', '2024-02'],
            'export_amount': [100.0, 200.0]
        })
        
        sorted_df = sort_by_date(df)
        
        self.assertListEqual(sorted_df['date'].tolist(), ['2024-01', '2024-02'])
    
    def test_index_reset(self):
        """인덱스가 리셋되는지 확인"""
        df = pd.DataFrame({
            'date': ['2024-02', '2024-01'],
            'export_amount': [200.0, 100.0]
        })
        
        sorted_df = sort_by_date(df)
        
        self.assertListEqual(sorted_df.index.tolist(), [0, 1])
    
    def test_empty_dataframe(self):
        """빈 DataFrame"""
        df = pd.DataFrame(columns=['date', 'export_amount'])
        result = sort_by_date(df)
        self.assertTrue(result.empty)
    
    def test_missing_date_column(self):
        """date 컬럼 누락"""
        df = pd.DataFrame({'export_amount': [100.0]})
        
        with self.assertRaises(ValueError):
            sort_by_date(df)


if __name__ == '__main__':
    unittest.main()
