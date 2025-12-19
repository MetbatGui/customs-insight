
import pandas as pd
import os
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import holidays
from datetime import date
import calendar

class DashboardGenerator:
    def enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates business days, daily average, MoM/YoY of daily average.
        """
        enriched = df.copy()
        kr_holidays = holidays.KR()
        
        # 1. Calculate Business Days & Daily Avg
        business_days_list = []
        daily_avg_list = []
        
        for _, row in enriched.iterrows():
            date_str = str(row.get('date', "")).replace('-', '/')
            amount = row.get('export_amount', 0)
            
            b_days = 0
            if len(date_str) == 7:
                try:
                    parts = date_str.split('/')
                    year = int(parts[0])
                    month = int(parts[1])
                    _, last_day = calendar.monthrange(year, month)
                    
                    count = 0
                    for day in range(1, last_day + 1):
                        d = date(year, month, day)
                        if d.weekday() >= 5: continue
                        if d in kr_holidays: continue
                        count += 1
                    b_days = count
                except ValueError:
                    pass
            
            d_avg = 0
            if b_days > 0:
                d_avg = round(amount / b_days)
            
            business_days_list.append(b_days)
            daily_avg_list.append(d_avg)
            
        enriched['business_days'] = business_days_list
        enriched['daily_avg'] = daily_avg_list
        
        # 2. MoM
        enriched['daily_avg_mom'] = enriched['daily_avg'].pct_change(periods=1) * 100
        enriched['daily_avg_mom'] = enriched['daily_avg_mom'].round(0)
        
        # 3. YoY
        enriched['temp_date'] = pd.to_datetime(enriched['date'].str.replace('/', '-') + '-01')
        df_prev = enriched[['temp_date', 'daily_avg']].copy()
        df_prev['match_date'] = df_prev['temp_date'] + pd.DateOffset(years=1)
        
        merged = pd.merge(
            enriched,
            df_prev[['match_date', 'daily_avg']],
            left_on='temp_date',
            right_on='match_date',
            how='left',
            suffixes=('', '_prev')
        )
        
        # Calculate YoY
        enriched['daily_avg_yoy'] = ((merged['daily_avg'] - merged['daily_avg_prev']) / merged['daily_avg_prev']) * 100
        enriched['daily_avg_yoy'] = enriched['daily_avg_yoy'].round(0)

        # 4. Quarterly Calculations (B & C columns)
        # Re-create temp_date/period for grouping if needed
        enriched['temp_date'] = pd.to_datetime(enriched['date'].str.replace('/', '-') + '-01')
        enriched['quarter'] = enriched['temp_date'].dt.to_period('Q')
        
        # Calculate sums per quarter
        # Logic Change: B column is Sum of Daily Avg (F) for the quarter
        quarterly_sums = enriched.groupby('quarter')[['daily_avg']].sum()
        
        # Calculate B and C values for the quarter
        # B: Quarter Daily Avg Sum = Sum(Daily Avg of months)
        quarterly_sums['quarter_b'] = quarterly_sums['daily_avg']
        
        # C: Quarter Avg = B / 3
        quarterly_sums['quarter_c'] = (quarterly_sums['quarter_b'] / 3).round(0)
        
        # Calculate Quarterly QoQ (D) and YoY (E)
        # QoQ: Compare with previous quarter (lag 1)
        quarterly_sums['quarter_qoq'] = quarterly_sums['quarter_c'].pct_change(periods=1) * 100
        quarterly_sums['quarter_qoq'] = quarterly_sums['quarter_qoq'].round(0)
        
        # YoY: Compare with same quarter last year (lag 4)
        quarterly_sums['quarter_yoy'] = quarterly_sums['quarter_c'].pct_change(periods=4) * 100
        quarterly_sums['quarter_yoy'] = quarterly_sums['quarter_yoy'].round(0)
        
        # Map back to the dataframe, but ONLY to the last month of each quarter
        enriched['quarter_b'] = None
        enriched['quarter_c'] = None
        enriched['quarter_d'] = None  # QoQ
        enriched['quarter_e'] = None  # YoY
        
        for q, row in quarterly_sums.iterrows():
            # Find the last month entry for this quarter in the enriched df
            # Filter by quarter
            q_mask = enriched['quarter'] == q
            if not q_mask.any():
                continue
                
            # Get index of the last date in this quarter
            # We assume data is sorted by date, but safer to pick max date
            last_idx = enriched[q_mask]['temp_date'].idxmax()
            
            # Check if this month is actually 3, 6, 9, 12? 
            # Or just the last available month in that quarter?
            last_date_in_q = enriched.loc[last_idx, 'temp_date']
            if last_date_in_q.month in [3, 6, 9, 12]:
                enriched.at[last_idx, 'quarter_b'] = row['quarter_b']
                enriched.at[last_idx, 'quarter_c'] = row['quarter_c']
                enriched.at[last_idx, 'quarter_d'] = row['quarter_qoq']
                enriched.at[last_idx, 'quarter_e'] = row['quarter_yoy']

        enriched = enriched.drop(columns=['temp_date', 'quarter'])
        
        return enriched

    def generate(self, source_file: str, data_df: pd.DataFrame, output_path: str) -> None:
        """
        Generates a dashboard Excel file.
        Expects data_df to be already enriched with business_days, daily_avg, etc.
        """
        # 1. Extract Title
        title = "Export Dashboard" 
        if os.path.exists(source_file):
            try:
                source_df = pd.read_excel(source_file, header=None, nrows=2)
                extracted_title = source_df.iloc[1, 0]
                if pd.notna(extracted_title):
                    title = str(extracted_title)
            except Exception as e:
                print(f"Warning: Could not extract title: {e}")
        
        # 2. Format Date for display
        df = data_df.copy()
        if 'date' in df.columns:
            df['date'] = df['date'].str.replace('-', '/')
        
        # 3. Setup Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Dashboard"
        
        ws['A1'] = title
        
        # Headers
        ws['A2'] = "Date"
        ws['B2'] = "분기(일평균합)"
        ws['C2'] = "분기(평균)"
        ws['D2'] = "QoQ"
        ws['E2'] = "YoY"
        ws['F2'] = "일평균 수출액(달러)"
        ws['G2'] = "MoM"
        ws['H2'] = "YoY"
        ws['I2'] = "Date"
        ws['J2'] = "금액(달러)"
        ws['K2'] = "영업일수"
        
        start_row = 3
        for idx, row_data in df.iterrows():
            current_row = start_row + idx
            
            date_str = row_data.get('date', "")
            amount_val = row_data.get('export_amount', 0)
            
            # Using enriched columns
            business_days = row_data.get('business_days', 0)
            daily_avg = row_data.get('daily_avg', 0)
            mom = row_data.get('daily_avg_mom', None)
            yoy = row_data.get('daily_avg_yoy', None)
            quarter_b = row_data.get('quarter_b', None)
            quarter_c = row_data.get('quarter_c', None)
            quarter_d = row_data.get('quarter_d', None)
            quarter_e = row_data.get('quarter_e', None)
            
            # Format percentages
            mom_str = f"{int(mom)}%" if pd.notna(mom) else None
            yoy_str = f"{int(yoy)}%" if pd.notna(yoy) else None
            q_d_str = f"{int(quarter_d)}%" if pd.notna(quarter_d) else None
            q_e_str = f"{int(quarter_e)}%" if pd.notna(quarter_e) else None
            
            # Write Cols
            ws.cell(row=current_row, column=1, value=date_str)   # A
            ws.cell(row=current_row, column=2, value=quarter_b)  # B
            ws.cell(row=current_row, column=3, value=quarter_c)  # C
            ws.cell(row=current_row, column=4, value=q_d_str)    # D
            ws.cell(row=current_row, column=5, value=q_e_str)    # E
            ws.cell(row=current_row, column=6, value=daily_avg)  # F
            ws.cell(row=current_row, column=7, value=mom_str)    # G
            ws.cell(row=current_row, column=8, value=yoy_str)    # H
            ws.cell(row=current_row, column=9, value=date_str)  # I
            ws.cell(row=current_row, column=10, value=amount_val) # J
            ws.cell(row=current_row, column=11, value=business_days) # K
                
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        wb.save(output_path)
