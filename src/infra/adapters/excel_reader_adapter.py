import pandas as pd
import os

class ExcelReaderAdapter:
    def read(self, file_path: str) -> pd.DataFrame:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        try:
            # header=[2, 3] means rows 3 and 4 (0-indexed 2, 3) are headers.
            # This handles the Year/Month -> Export/Import -> Amount/Weight structure.
            df = pd.read_excel(file_path, header=[2, 3])
            return df
        except Exception as e:
            raise Exception(f"Error reading excel file: {e}")