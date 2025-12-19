import unittest
import os
import pandas as pd
from returns.result import Success, Failure
from src.infra.adapters.excel_reader_adapter import (
    ExcelReaderAdapter,
    read_excel_safe,
    read_excel_with_fallback
)

class TestExcelReaderAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = ExcelReaderAdapter()
        # Ensure the path is correct relative to where the test is run
        # Assuming run from project root
        self.file_path = 'data/수출입통계 상세조회 팝업.xlsx'

    def test_read_excel_file_exists(self):
        """Test if the file exists and is readable"""
        if not os.path.exists(self.file_path):
            self.skipTest(f"Test file not found at {self.file_path}")
            
        df = self.adapter.read(self.file_path)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty, "DataFrame should not be empty")
        
        print("\n--- Test Output: First 5 rows ---")
        print(df.head().to_string())
        print("---------------------------------")

    def test_file_not_found(self):
        """Test behavior when file does not exist"""
        with self.assertRaises(FileNotFoundError):
            self.adapter.read('non_existent_file.xlsx')


class TestReadExcelSafe(unittest.TestCase):
    """Result 타입 함수 테스트"""
    
    def test_file_not_found_returns_failure(self):
        """파일이 없으면 Failure 반환"""
        result = read_excel_safe('non_existent_file.xlsx')
        
        self.assertIsInstance(result, Failure)
        error_msg = result.failure()
        self.assertIn("File not found", error_msg)
    
    def test_success_case_returns_dataframe(self):
        """파일이 있으면 Success[DataFrame] 반환"""
        file_path = 'data/수출입통계 상세조회 팝업.xlsx'
        
        if not os.path.exists(file_path):
            self.skipTest(f"Test file not found at {file_path}")
        
        result = read_excel_safe(file_path)
        
        self.assertIsInstance(result, Success)
        df = result.unwrap()
        self.assertIsInstance(df, pd.DataFrame)
    
    def test_result_mapping(self):
        """Result.map()로 함수형 처리"""
        file_path = 'data/수출입통계 상세조회 팝업.xlsx'
        
        if not os.path.exists(file_path):
            self.skipTest(f"Test file not found at {file_path}")
        
        result = read_excel_safe(file_path)
        
        # Success인 경우에만 shape 반환
        shape_result = result.map(lambda df: df.shape)
        
        self.assertIsInstance(shape_result, Success)
        shape = shape_result.unwrap()
        self.assertIsInstance(shape, tuple)
        self.assertEqual(len(shape), 2)
    
    def test_result_chaining(self):
        """Result.bind()로 체이닝"""
        file_path = 'data/수출입통계 상세조회 팝업.xlsx'
        
        if not os.path.exists(file_path):
            self.skipTest(f"Test file not found at {file_path}")
        
        def get_first_5_rows(df: pd.DataFrame) -> pd.DataFrame:
            return df.head(5)
        
        result = (
            read_excel_safe(file_path)
            .map(get_first_5_rows)
            .map(lambda df: len(df))
        )
        
        if isinstance(result, Success):
            self.assertLessEqual(result.unwrap(), 5)


class TestAdapterNewInterface(unittest.TestCase):
    """ExcelReaderAdapter의 새로운 read_safe 인터페이스 테스트"""
    
    def test_read_safe_returns_result(self):
        """read_safe는 Result 타입 반환"""
        adapter = ExcelReaderAdapter()
        result = adapter.read_safe('non_existent.xlsx')
        
        self.assertIsInstance(result, Failure)
    
    def test_backward_compatibility(self):
        """기존 read() 메서드는 여전히 Exception raise"""
        adapter = ExcelReaderAdapter()
        
        with self.assertRaises(FileNotFoundError):
            adapter.read('non_existent.xlsx')


if __name__ == '__main__':
    unittest.main()
