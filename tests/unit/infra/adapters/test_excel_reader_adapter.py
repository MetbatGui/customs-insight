import unittest
import os
import pandas as pd
from src.infra.adapters.excel_reader_adapter import ExcelReaderAdapter

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

if __name__ == '__main__':
    unittest.main()
