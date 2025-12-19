import pandas as pd
import re

class DataProcessor:
    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        # 1. Select relevant columns (Period, Export Amount)
        # Assuming column 0 is Period, Column 1 is Export Amount based on inspection
        # MultiIndex columns can be tricky, so we access by position
        df_selected = df.iloc[:, [0, 1]].copy()
        df_selected.columns = ['period_raw', 'export_amount']

        # 2. Parse Dates and Filter
        processed_data = []
        current_year = None

        for index, row in df_selected.iterrows():
            period_val = str(row['period_raw']).strip()
            
            # Check for Year (e.g., "2025년")
            year_match = re.match(r'(\d{4})년', period_val)
            if year_match:
                current_year = year_match.group(1)
                continue
            
            # Check for Month (e.g., "01월")
            month_match = re.match(r'(\d{1,2})월', period_val)
            if month_match and current_year:
                month = month_match.group(1).zfill(2)
                date_str = f"{current_year}-{month}"
                
                try:
                    amount = float(row['export_amount'])
                except (ValueError, TypeError):
                    amount = 0.0

                processed_data.append({
                    'date': date_str,
                    'export_amount': amount
                })

        # Create new DataFrame
        result_df = pd.DataFrame(processed_data)
        
        # Aggregate by Date (Sum) to handle multiple entries per month (e.g. from different regions)
        if not result_df.empty:
            result_df = result_df.groupby('date', as_index=False)['export_amount'].sum()
        
        # Sort by date
        result_df = result_df.sort_values('date').reset_index(drop=True)

        # 3. Calculate MoM and YoY
        # MoM: Compare with previous row (lag 1)
        # We assume sorted by date.
        result_df['export_mom'] = result_df['export_amount'].pct_change(periods=1) * 100
        
        # YoY: Robust calculation using date matching
        # 1. Convert to real datetime to safely manipulate dates
        result_df['temp_date'] = pd.to_datetime(result_df['date'] + '-01')
        
        # 2. Create a lookup for previous year values
        # We want to find the amount where date is (current_date - 1 year)
        df_prev = result_df[['temp_date', 'export_amount']].copy()
        df_prev['match_date'] = df_prev['temp_date'] + pd.DateOffset(years=1)
        
        # 3. Merge original with shifted
        merged = pd.merge(
            result_df, 
            df_prev[['match_date', 'export_amount']], 
            left_on='temp_date', 
            right_on='match_date', 
            how='left', 
            suffixes=('', '_prev_year')
        )
        
        # 4. Calculate YoY
        merged['export_yoy'] = ((merged['export_amount'] - merged['export_amount_prev_year']) / merged['export_amount_prev_year']) * 100
        
        # 5. Clean up
        result_df['export_yoy'] = merged['export_yoy']
        result_df = result_df.drop(columns=['temp_date'])

        # Round for display
        result_df['export_mom'] = result_df['export_mom'].round(2)
        result_df['export_yoy'] = result_df['export_yoy'].round(2)

        return result_df

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


