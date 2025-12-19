import pandas as pd
import re

class DataProcessor:
    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """DataFrame을 처리하여 월별 수출 데이터와 MoM/YoY를 계산합니다.
        
        기존의 긴 메서드를 순수 함수 파이프라인으로 교체하여 SRP를 준수합니다.
        내부적으로 domain.calculations 모듈의 순수 함수들을 사용합니다.
        
        Args:
            df: 원본 DataFrame (MultiIndex 헤더 포함)
            
        Returns:
            처리된 DataFrame (date, export_amount, export_mom, export_yoy 컬럼)
            
        Examples:
            >>> processor = DataProcessor()
            >>> result_df = processor.process(raw_df)
            >>> print(result_df.columns)
            ['date', 'export_amount', 'export_mom', 'export_yoy']
        """
        from ..calculations.pipeline import process_trade_data
        
        # 기존 순수 함수 파이프라인 사용 (Phase 3에서 작성됨)
        return process_trade_data(df)

    def filter_by_year(self, df: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
        """Filter DataFrame by year range (inclusive)."""
        # Convert date column to datetime for easier extracting
        # Note: 'date' col is string "YYYY-MM"
        temp_date = pd.to_datetime(df['date'] + '-01')
        
        # Create mask
        mask = (temp_date.dt.year >= start_year) & (temp_date.dt.year <= end_year)
        
        return df.loc[mask].reset_index(drop=True)

    def process_quarterly(self, monthly_df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregates monthly data into quarterly data and calculates QoQ and YoY.
        Expects monthly_df to have 'date' (YYYY-MM) and 'export_amount' columns.
        """
        if monthly_df.empty:
            return pd.DataFrame(columns=['quarter', 'export_amount', 'export_qoq', 'export_yoy'])

        df = monthly_df.copy()
        
        # Convert date to datetime
        df['temp_date'] = pd.to_datetime(df['date'] + '-01')
        
        # Determine Quarter (e.g., '2024Q1')
        df['quarter'] = df['temp_date'].dt.to_period('Q').astype(str)
        
        # Aggregate by Quarter
        quarterly_df = df.groupby('quarter')['export_amount'].sum().reset_index()
        
        # Sort by quarter
        quarterly_df = quarterly_df.sort_values('quarter').reset_index(drop=True)
        
        # Calculate QoQ (Quarter-over-Quarter) - Lag 1 quarter
        quarterly_df['export_qoq'] = quarterly_df['export_amount'].pct_change(periods=1) * 100
        
        # Calculate YoY (Year-over-Year) - Lag 4 quarters (since there are 4 quarters in a year)
        # Assuming continuous quarters. If there are gaps, we need a robust merge approach similar to monthly.
        
        # Robust YoY Calculation
        # 1. Convert quarter string back to period for easier math
        quarterly_df['period_obj'] = pd.PeriodIndex(quarterly_df['quarter'], freq='Q')
        
        # 2. Self-merge to find previous year's same quarter
        df_prev = quarterly_df[['period_obj', 'export_amount']].copy()
        df_prev['match_period'] = df_prev['period_obj'] + 4  # e.g. 2023Q1 + 4 = 2024Q1
        
        merged = pd.merge(
            quarterly_df,
            df_prev[['match_period', 'export_amount']],
            left_on='period_obj',
            right_on='match_period',
            how='left',
            suffixes=('', '_prev_year')
        )
        
        quarterly_df['export_yoy'] = ((merged['export_amount'] - merged['export_amount_prev_year']) / merged['export_amount_prev_year']) * 100
        
        # Clean up
        quarterly_df = quarterly_df.drop(columns=['period_obj'])
        
        # Rounding
        quarterly_df['export_qoq'] = quarterly_df['export_qoq'].round(2)
        quarterly_df['export_yoy'] = quarterly_df['export_yoy'].round(2)
        
        return quarterly_df

    def filter_quarterly_by_year(self, df: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
        """Filter Quarterly DataFrame by year range (inclusive)."""
        # Quarter is string like '2023Q1'
        # Extract year
        df_copy = df.copy()
        df_copy['temp_year'] = df_copy['quarter'].astype(str).str[:4].astype(int)
        
        mask = (df_copy['temp_year'] >= start_year) & (df_copy['temp_year'] <= end_year)
        
        return df_copy.loc[mask].drop(columns=['temp_year']).reset_index(drop=True)


