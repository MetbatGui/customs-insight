"""
StrategyExecutor - Strategy 객체 기반 스크래핑 실행 서비스

Strategy 객체를 받아 각 품목을 순회하며 필터를 적용하고 데이터를 다운로드합니다.
검증된 Playwright selector를 사용하여 실제 스크래핑을 수행합니다.
"""

import time
import os
from typing import List
from playwright.sync_api import Page
from src.domain.models import Strategy, StrategyItem, DomesticRegionFilter, CustomsOfficeFilter


class StrategyExecutor:
    """
    Strategy 객체 기반 스크래핑 실행 서비스
    
    Strategy 객체를 받아 각 품목을 순회하며
    필터를 적용하고 데이터를 다운로드합니다.
    
    Example:
        >>> executor = StrategyExecutor()
        >>> results = executor.execute(page, "data", strategy)
        >>> print(results)
        ['data/에이피알_화장품.xlsx', 'data/에이피알_미용기기.xlsx']
    """
    
    def execute(self, page: Page, save_dir: str, strategy: Strategy) -> List[str]:
        """
        Strategy 실행
        
        Args:
            page: Playwright Page 객체
            save_dir: 저장 디렉토리
            strategy: Strategy 객체
            
        Returns:
            다운로드된 파일 경로 리스트
        """
        print(f"\n{'='*60}")
        print(f"[StrategyExecutor] Executing Strategy: {strategy.name}")
        print(f"{'='*60}")
        
        # Page navigation
        url = "https://www.bandtrass.or.kr/customs/total.do?command=CUS001View&viewCode=CUS00301"
        print(f"[Navigation] Navigating to {url}")
        page.goto(url)
        page.wait_for_load_state('networkidle')
        
        results = []
        
        for idx, item in enumerate(strategy.items, 1):
            print(f"\n--- Item {idx}/{len(strategy.items)}: {item.name} ---")
            
            # 1-6: 품목 검색
            self._search_item(page, item)
            
            # 7-10: 필터 적용 및 조회
            if item.filters:
                self._apply_filters(page, item.filters)
            else:
                # 필터 없으면 바로 조회
                print("  [Note] No filters to apply, proceeding to search")
                page.locator('button[onclick*="goSearch"]').click()
                page.wait_for_timeout(3000)
            
            # 11-13: 데이터 다운로드
            file_path = self._download_data(page, save_dir, strategy.name, item.name)
            results.append(file_path)
        
        print(f"\n{'='*60}")
        print(f"[StrategyExecutor] Completed: {len(results)} files downloaded")
        print(f"{'='*60}\n")
        
        return results
    
    def _search_item(self, page: Page, item: StrategyItem):
        """
        품목 검색 (1-6단계)
        
        Args:
            page: Playwright Page 객체
            item: StrategyItem 객체
        """
        # [1] 품목/성질별 버튼 클릭
        print(f"  [1] Clicking '품목/성질별'")
        page.locator('div#GODS_DIV').click()
        page.wait_for_selector('#GODS_TYPE',  state='visible')
        
        # [2] 드롭다운에서 '품목' 선택
        print(f"  [2] Selecting '품목' from dropdown")
        page.select_option('#GODS_TYPE', value='H')
        page.wait_for_timeout(500)
        
        # [3] '품목 검색하기' 버튼 클릭
        print(f"  [3] Clicking '품목 검색하기'")
        page.locator('span#POPUP1').click()
        
        # 팝업 대기 및 처리
        popup = page.wait_for_event('popup')
        popup.wait_for_load_state()
        
        # [4] HS Code 입력
        print(f"  [4] Entering HS Code: {item.hs_code}")
        popup.locator('input#CustomText').fill(item.hs_code)
        popup.wait_for_timeout(500)
        
        # [5] 직접입력추가 버튼 클릭
        print(f"  [5] Clicking '직접입력추가'")
        popup.locator('button#CustomCheck').click()
        popup.wait_for_timeout(1000)
        
        # [6] 선택적용 버튼 클릭
        print(f"  [6] Clicking '선택적용'")
        popup.locator('button[onclick="fn_ok();"]').click()
        
        # 팝업 닫힐 때까지 대기
        popup.wait_for_event('close', timeout=5000)
        page.wait_for_timeout(1000)
    
    def _apply_filters(self, page: Page, filters):
        """
        필터 적용 (7-10단계)
        
        Args:
            page: Playwright Page 객체
            filters: 필터 리스트
        """
        for filter in filters:
            if isinstance(filter, DomesticRegionFilter):
                self._apply_domestic_region_filter(page, filter)
            elif isinstance(filter, CustomsOfficeFilter):
                self._apply_customs_office_filter(page, filter)
    
    def _apply_domestic_region_filter(self, page: Page, filter: DomesticRegionFilter):
        """
        국내지역 필터 적용
        
        Args:
            page: Playwright Page 객체
            filter: DomesticRegionFilter 객체
        """
        # [7] 국내지역 필터 선택
        print(f"  [7] Selecting '국내지역' filter")
        page.locator('div#LOCATION_DIV').click()
        page.wait_for_selector('#LOCATION_TYPE', state='visible')
        
        # [8] Scope 선택 (시, 시군구, etc.)
        print(f"  [8] Selecting scope: '{filter.scope}'")
        scope_value = {'시': 'A', '시군구': 'B'}.get(filter.scope, 'A')
        page.select_option('#LOCATION_TYPE', value=scope_value)
        page.wait_for_timeout(1000)
        
        # [9] 지역 선택
        for region in filter.regions:
            print(f"  [9] Selecting region: '{region}'")
            # multiselect 드롭다운에서 지역 선택
            page.locator('select#Select2').select_option(label=region)
            page.wait_for_timeout(500)
        
        # [10] 조회하기 버튼 클릭
        print(f"  [10] Clicking '조회하기'")
        page.locator('button[onclick*="goSearch"]').click()
        
        # 결과 테이블 로드 대기
        page.wait_for_selector('#table_list_1 tr.jqgrow', timeout=10000)
        page.wait_for_timeout(2000)
    
    def _apply_customs_office_filter(self, page: Page, filter: CustomsOfficeFilter):
        """
        세관 필터 적용
        
        Args:
            page: Playwright Page 객체
            filter: CustomsOfficeFilter 객체
        """
        # TODO: 세관 필터 구현 필요
        print(f"  [7] Selecting '세관' filter")
        print(f"  [8-9] Customs office filter: {filter.customs_offices}")
        print(f"  [10] Clicking '조회하기'")
        
        # 임시로 조회하기만 클릭
        page.locator('button[onclick*="goSearch"]').click()
        page.wait_for_selector('#table_list_1 tr.jqgrow', timeout=10000)
        page.wait_for_timeout(2000)
    
    def _download_data(self, page: Page, save_dir: str, strategy_name: str, item_name: str) -> str:
        """
        데이터 다운로드 (11-13단계)
        
        Args:
            page: Playwright Page 객체
            save_dir: 저장 디렉토리
            strategy_name: 전략 이름
            item_name: 품목 이름
            
        Returns:
            다운로드된 파일 경로
        """
        # [11] 첫 번째 행의 수출 금액 셀 클릭
        print(f"  [11] Clicking first row's export amount cell")
        export_amt_cell = page.locator('td[aria-describedby="table_list_1_EX_AMT"] font').first
        export_amt_cell.wait_for()
        export_amt_cell.click()
        page.wait_for_timeout(2000)
        
        # [12] 다운로드 버튼 클릭
        print(f"  [12] Clicking download button")
        download_btn = page.locator('a[href*="GridtoExcel"]')
        download_btn.wait_for()
        
        # 다운로드 시작
        download = page.expect_download()
        download_btn.click()
        download_info = download.value
        
        # [13] 얼럿 자동 수락 (이미 page.on('dialog') 설정됨)
        print(f"  [13] Download accepted")
        
        # 파일 저장
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, f"{strategy_name}_{item_name}.xlsx")
        download_info.save_as(file_path)
        
        print(f"  → Downloaded: {file_path}")
        
        return file_path
