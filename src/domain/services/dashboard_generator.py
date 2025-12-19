import pandas as pd
import os
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import holidays
from datetime import date
import calendar


class DashboardGenerator:
    """대시보드 Excel 파일을 생성하는 제너레이터입니다.
    
    월별 수출 데이터를 읽어 영업일 기준 일평균을 계산하고,
    분기별 통계와 함께 대시보드 형식의 Excel 파일을 생성합니다.
    
    주요 기능:
        - 영업일(평일-공휴일) 계산
        - 일평균 수출액 계산 (월 수출액 / 영업일)
        - 일평균 MoM/YoY 증감률 계산
        - 분기별 통계 계산 및 표시
        - openpyxl을 사용한 대시보드 레이아웃 생성
    
    Examples:
        >>> generator = DashboardGenerator()
        >>> enriched_df = generator.enrich_data(monthly_df)
        >>> generator.generate("source.xlsx", enriched_df, "dashboard.xlsx")
    """
    
    def enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """월별 데이터에 영업일, 일평균, 증감률, 분기별 통계를 추가합니다.
        
        원본 월별 수출 데이터에 다음 컬럼들을 추가하여 반환합니다:
        - business_days: 영업일 수 (평일 - 한국 공휴일)
        - daily_avg: 일평균 수출액
        - daily_avg_mom: 일평균 전월 대비 증감률
        - daily_avg_yoy: 일평균 전년 동기 대비 증감률
        - quarter_b, quarter_c, quarter_d, quarter_e: 분기별 통계
        
        Args:
            df: 월별 DataFrame. 다음 컬럼을 포함해야 합니다:
                - date (str): 날짜 (YYYY/MM 또는 YYYY-MM 형식)
                - export_amount (float): 월별 수출액
        
        Returns:
            enriched DataFrame. 원본 컬럼에 추가된 통계 컬럼들을 포함합니다.
        
        Examples:
            >>> generator = DashboardGenerator()
            >>> enriched = generator.enrich_data(monthly_df)
            >>> print(enriched.columns)
            ['date', 'export_amount', 'export_mom', 'export_yoy',
             'business_days', 'daily_avg', 'daily_avg_mom', 'daily_avg_yoy',
             'quarter_b', 'quarter_c', 'quarter_d', 'quarter_e']
        
        Note:
            - 영업일은 한국 공휴일(holidays.KR)을 고려하여 계산됩니다.
            - 분기별 통계는 3, 6, 9, 12월 행에만 표시됩니다.
            - 이 메서드는 내부적으로 4개의 하위 메서드를 호출합니다.
            - generate() 메서드에서 칼럼명을 한글로 변환합니다.
        """
        enriched = df.copy()
        
        enriched = self._add_business_days_and_daily_avg(enriched)
        enriched = self._add_daily_avg_mom(enriched)
        enriched = self._add_daily_avg_yoy(enriched)
        enriched = self._add_quarterly_stats(enriched)
        
        return enriched
    
    def _add_business_days_and_daily_avg(self, df: pd.DataFrame) -> pd.DataFrame:
        """영업일 수와 일평균 수출액을 계산하여 추가합니다.
        
        각 월의 영업일 수를 계산하고 (평일 - 한국 공휴일),
        월 수출액을 영업일로 나누어 일평균을 계산합니다.
        
        Args:
            df: 월별 DataFrame (date, export_amount 포함).
        
        Returns:
            business_days와 daily_avg 컬럼이 추가된 DataFrame.
        
        Note:
            - 토요일, 일요일은 제외됩니다.
            - 한국 공휴일(holidays.KR)도 제외됩니다.
            - 영업일이 0인 경우 일평균은 0입니다.
        """
        enriched = df.copy()
        kr_holidays = holidays.KR()
        
        business_days_list = []
        daily_avg_list = []
        
        for _, row in enriched.iterrows():
            date_str = str(row.get('date', '')).replace('-', '/')
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
                        if d.weekday() >= 5:
                            continue
                        if d in kr_holidays:
                            continue
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
        
        return enriched
    
    def _add_daily_avg_mom(self, df: pd.DataFrame) -> pd.DataFrame:
        """일평균의 전월 대비(MoM) 증감률을 계산하여 추가합니다.
        
        Args:
            df: daily_avg 컬럼을 포함한 DataFrame.
        
        Returns:
            daily_avg_mom 컬럼이 추가된 DataFrame.
        
        Note:
            - 첫 번째 행은 NaN입니다 (비교 대상이 없음).
            - 결과는 정수로 반올림됩니다.
        """
        enriched = df.copy()
        enriched['daily_avg_mom'] = enriched['daily_avg'].pct_change(periods=1) * 100
        enriched['daily_avg_mom'] = enriched['daily_avg_mom'].round(0)
        return enriched
    
    def _add_daily_avg_yoy(self, df: pd.DataFrame) -> pd.DataFrame:
        """일평균의 전년 동기 대비(YoY) 증감률을 계산하여 추가합니다.
        
        Args:
            df: date와 daily_avg 컬럼을 포함한 DataFrame.
        
        Returns:
            daily_avg_yoy 컬럼이 추가된 DataFrame.
        
        Note:
            - 정확히 1년 전 데이터를 매칭하여 계산합니다.
            - 매칭되지 않으면 NaN입니다.
            - 결과는 정수로 반올림됩니다.
        """
        enriched = df.copy()
        
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
        
        enriched['daily_avg_yoy'] = ((merged['daily_avg'] - merged['daily_avg_prev']) / merged['daily_avg_prev']) * 100
        enriched['daily_avg_yoy'] = enriched['daily_avg_yoy'].round(0)
        enriched = enriched.drop(columns=['temp_date'])
        
        return enriched
    
    def _add_quarterly_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """분기별 통계를 계산하여 분기 마지막 월(3, 6, 9, 12월)에 추가합니다.
        
        분기별로 다음 통계를 계산합니다:
        - quarter_b: 분기 내 일평균 합계
        - quarter_c: 분기 평균 (quarter_b / 3)
        - quarter_d: QoQ (전 분기 대비 증감률)
        - quarter_e: YoY (전년 동기 분기 대비 증감률)
        
        Args:
            df: date와 daily_avg 컬럼을 포함한 DataFrame.
        
        Returns:
            분기별 통계 컬럼(quarter_b, c, d, e)이 추가된 DataFrame.
            통계는 각 분기 마지막 월(3, 6, 9, 12월)에만 표시되고,
            다른 월은 None입니다.
        
        Note:
            - 분기 마지막 월이 데이터에 없으면 해당 분기 통계는 표시되지 않습니다.
            - QoQ는 전 분기의 quarter_c와 비교합니다.
            - YoY는 4분기 전(1년 전)의 quarter_c와 비교합니다.
        """
        enriched = df.copy()
        
        enriched['temp_date'] = pd.to_datetime(enriched['date'].str.replace('/', '-') + '-01')
        enriched['quarter'] = enriched['temp_date'].dt.to_period('Q')
        
        quarterly_sums = enriched.groupby('quarter')[['daily_avg']].sum()
        quarterly_sums['quarter_b'] = quarterly_sums['daily_avg']
        quarterly_sums['quarter_c'] = (quarterly_sums['quarter_b'] / 3).round(0)
        
        quarterly_sums['quarter_qoq'] = quarterly_sums['quarter_c'].pct_change(periods=1) * 100
        quarterly_sums['quarter_qoq'] = quarterly_sums['quarter_qoq'].round(0)
        
        quarterly_sums['quarter_yoy'] = quarterly_sums['quarter_c'].pct_change(periods=4) * 100
        quarterly_sums['quarter_yoy'] = quarterly_sums['quarter_yoy'].round(0)
        
        enriched['quarter_b'] = None
        enriched['quarter_c'] = None
        enriched['quarter_d'] = None
        enriched['quarter_e'] = None
        
        for q, row in quarterly_sums.iterrows():
            q_mask = enriched['quarter'] == q
            if not q_mask.any():
                continue
            
            last_idx = enriched[q_mask]['temp_date'].idxmax()
            last_date_in_q = enriched.loc[last_idx, 'temp_date']
            
            if last_date_in_q.month in [3, 6, 9, 12]:
                enriched.at[last_idx, 'quarter_b'] = row['quarter_b']
                enriched.at[last_idx, 'quarter_c'] = row['quarter_c']
                enriched.at[last_idx, 'quarter_d'] = row['quarter_qoq']
                enriched.at[last_idx, 'quarter_e'] = row['quarter_yoy']
        
        enriched = enriched.drop(columns=['temp_date', 'quarter'])
        
        return enriched
    
    def generate(self, source_file: str, data_df: pd.DataFrame, output_path: str):
        """대시보드 Excel 파일을 생성합니다.
        
        enriched DataFrame을 받아 openpyxl을 사용하여
        대시보드 형식의 Excel 파일을 생성합니다.
        칼럼명을 한글로 변환하여 가독성을 높입니다.
        
        Args:
            source_file: 원본 파일 경로 (제목에 표시용).
            data_df: enrich_data()로 처리된 DataFrame.
                    business_days, daily_avg 등의 컬럼을 포함해야 합니다.
            output_path: 생성할 대시보드 파일 경로.
        
        Note:
            - A1 셀에 제목이 표시됩니다.
            - A2부터 헤더가 시작됩니다.
            - 모든 칼럼명이 한글로 변환됩니다.
            - openpyxl Workbook을 사용하여 레이아웃을 구성합니다.
        """
        column_mapping = {
            'date': '날짜',
            'export_amount': '수출액(달러)',
            'export_mom': 'MoM(%)',
            'export_yoy': 'YoY(%)',
            'business_days': '영업일',
            'daily_avg': '일평균(달러)',
            'daily_avg_mom': '일평균 MoM(%)',
            'daily_avg_yoy': '일평균 YoY(%)',
            'quarter_b': '분기합계(B)',
            'quarter_c': '분기평균(C)',
            'quarter_d': 'QoQ(%)',
            'quarter_e': '분기 YoY(%)'
        }
        
        display_df = data_df.copy()
        display_df = display_df.rename(columns=column_mapping)
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Dashboard"
        
        ws.append([f"Dashboard - {os.path.basename(source_file)}"])
        
        headers = list(display_df.columns)
        ws.append(headers)
        
        for row in dataframe_to_rows(display_df, index=False, header=False):
            ws.append(row)
        
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        wb.save(output_path)
