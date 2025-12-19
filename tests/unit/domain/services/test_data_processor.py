import unittest
import pandas as pd
import numpy as np
from src.domain.services.data_processor import DataProcessor

class TestDataProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = DataProcessor()

    def test_process_logic(self):
        # Create a mock dataframe simulating the Excel structure
        # Columns: Period, Exp Amt, Exp Wgt, Imp Amt, Imp Wgt
        data = {
            'period': ['2023년', '01월', '02월', '2024년', '01월', '02월'],
            'exp_amt': [None, 100, 200, None, 150, 220],
            'exp_wgt': [None, 10, 20, None, 15, 22],
            'imp_amt': [None, 50, 50, None, 60, 60],
            'imp_wgt': [None, 5, 5, None, 6, 6]
        }
        df = pd.DataFrame(data)
        
        result = self.processor.process(df)
        
        # Check columns
        expected_cols = ['date', 'export_amount', 'export_mom', 'export_yoy']
        self.assertListEqual(list(result.columns), expected_cols)
        
        # Check rows count (should be 4 months: 2023-01, 02, 2024-01, 02)
        self.assertEqual(len(result), 4)
        
        # Check Values
        # 2023-01: 100. MoM NaN, YoY NaN
        self.assertEqual(result.iloc[0]['date'], '2023-01')
        self.assertEqual(result.iloc[0]['export_amount'], 100)
        self.assertTrue(np.isnan(result.iloc[0]['export_mom']))
        
        # 2023-02: 200. MoM: (200-100)/100 = 100%
        self.assertEqual(result.iloc[1]['date'], '2023-02')
        self.assertEqual(result.iloc[1]['export_amount'], 200)
        self.assertEqual(result.iloc[1]['export_mom'], 100.0)
        
        # 2024-01: 150. YoY vs 2023-01 (100) -> 50%
        # MoM vs 2023-02 (200) -> (150-200)/200 = -25%
        self.assertEqual(result.iloc[2]['date'], '2024-01')
        self.assertEqual(result.iloc[2]['export_amount'], 150)
        self.assertEqual(result.iloc[2]['export_mom'], -25.0)
        self.assertEqual(result.iloc[2]['export_yoy'], 50.0)

    def test_process_quarterly_logic(self):
        # Create monthly data spanning multiple quarters/years
        data = [
            {'date': '2023-01', 'export_amount': 100},
            {'date': '2023-02', 'export_amount': 100},
            {'date': '2023-03', 'export_amount': 100}, # Q1 Total: 300
            {'date': '2023-04', 'export_amount': 200},
            {'date': '2023-05', 'export_amount': 200},
            {'date': '2023-06', 'export_amount': 200}, # Q2 Total: 600. QoQ: (600-300)/300 = 100%
            {'date': '2024-01', 'export_amount': 150},
            {'date': '2024-02', 'export_amount': 150},
            {'date': '2024-03', 'export_amount': 150}, # 2024 Q1 Total: 450. YoY vs 2023 Q1 (300) = 50%
        ]
        monthly_df = pd.DataFrame(data)
        
        result = self.processor.process_quarterly(monthly_df)
        
        # Expected rows: 2023Q1, 2023Q2, 2024Q1
        self.assertEqual(len(result), 3)
        
        # Check 2023Q1
        row1 = result.iloc[0]
        self.assertEqual(str(row1['quarter']), '2023Q1')
        self.assertEqual(row1['export_amount'], 300)
        self.assertTrue(np.isnan(row1['export_qoq']))
        self.assertTrue(np.isnan(row1['export_yoy']))
        
        # Check 2023Q2
        row2 = result.iloc[1]
        self.assertEqual(str(row2['quarter']), '2023Q2')
        self.assertEqual(row2['export_amount'], 600)
        self.assertEqual(row2['export_qoq'], 100.0)
        
        # Check 2024Q1
        row3 = result.iloc[2]
        self.assertEqual(str(row3['quarter']), '2024Q1')
        self.assertEqual(row3['export_amount'], 450)
        self.assertEqual(row3['export_yoy'], 50.0)

if __name__ == '__main__':
    unittest.main()
