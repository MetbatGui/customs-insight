import pandas as pd
import re
from src.domain.calculations.pipeline import process_trade_data

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
        # 기존 순수 함수 파이프라인 사용 (Phase 3에서 작성됨)
        return process_trade_data(df)

    def filter_by_year(self, df: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
        """연도 범위로 월별 DataFrame을 필터링합니다.
        
        Args:
            df: 필터링할 DataFrame (date, export_amount 등 포함)
            start_year: 시작 연도 (포함)
            end_year: 종료 연도 (포함)
            
        Returns:
            필터링된 DataFrame
            
        Examples:
            >>> processor = DataProcessor()
            >>> filtered = processor.filter_by_year(df, 2024, 2025)
        """
        # date 컬럼은 "YYYY-MM" 형식의 문자열
        temp_date = pd.to_datetime(df['date'] + '-01')
        mask = (temp_date.dt.year >= start_year) & (temp_date.dt.year <= end_year)
        return df.loc[mask].reset_index(drop=True)

    def process_quarterly(self, monthly_df: pd.DataFrame) -> pd.DataFrame:
        """월별 데이터를 분기별로 집계하고 QoQ/YoY를 계산합니다.
        
        Args:
            monthly_df: 월별 DataFrame (date, export_amount 컬럼 필요)
                       date는 'YYYY-MM' 형식의 문자열
            
        Returns:
            분기별 DataFrame (quarter, export_amount, export_qoq, export_yoy)
            
        Examples:
            >>> processor = DataProcessor()
            >>> quarterly = processor.process_quarterly(monthly_df)
            >>> print(quarterly.columns)
            ['quarter', 'export_amount', 'export_qoq', 'export_yoy']
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
        """연도 범위로 분기별 DataFrame을 필터링합니다.
        
        Args:
            df: 필터링할 DataFrame (quarter 컬럼 필요)
            start_year: 시작 연도 (포함)
            end_year: 종료 연도 (포함)
            
        Returns:
            필터링된 분기별 DataFrame
            
        Examples:
            >>> processor = DataProcessor()
            >>> filtered = processor.filter_quarterly_by_year(quarterly_df, 2024, 2025)
        """
        # quarter는 '2023Q1' 형식의 문자열
        df_copy = df.copy()
        df_copy['temp_year'] = df_copy['quarter'].astype(str).str[:4].astype(int)
        mask = (df_copy['temp_year'] >= start_year) & (df_copy['temp_year'] <= end_year)
        return df_copy.loc[mask].drop(columns=['temp_year']).reset_index(drop=True)


