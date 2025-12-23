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
        
        # Strategy 세부정보 출력
        import json
        strategy_dict = strategy.model_dump()
        print(f"\n[Strategy Details]")
        print(json.dumps(strategy_dict, indent=2, ensure_ascii=False))
        print(f"\n{'='*60}\n")
        
        results = []
        
        for idx, item in enumerate(strategy.items, 1):
            print(f"\n--- Item {idx}/{len(strategy.items)}: {item.name} ---")
            print(f"  HS Code: {item.hs_code}")
            print(f"  Filters: {len(item.filters)} filter(s)")
            
            # 지역 필터를 분리하여 각 지역마다 개별 다운로드
            # isinstance가 모듈 경로 차이로 False가 될 수 있으므로 타입 이름으로 체크
            region_filters = [f for f in item.filters if type(f).__name__ == 'DomesticRegionFilter']
            other_filters = [f for f in item.filters if type(f).__name__ != 'DomesticRegionFilter']
            
            print(f"  → Region filters found: {len(region_filters)}")
            if region_filters:
                print(f"  → Regions in filter: {region_filters[0].regions}")
            
            # 지역 필터가 있고 여러 지역이 있는 경우, 각 지역마다 개별 다운로드
            if region_filters and len(region_filters[0].regions) > 1:
                region_filter = region_filters[0]
                print(f"  → Multiple regions detected: {region_filter.regions}")
                print(f"  → Will download separately for each region")
                
                for region_idx, region in enumerate(region_filter.regions, 1):
                    print(f"\n  === Region {region_idx}/{len(region_filter.regions)}: {region} ===")
                    
                    # 페이지 새로 로드
                    url = "https://www.bandtrass.or.kr/customs/total.do?command=CUS001View&viewCode=CUS00301"
                    print(f"  [Navigation] Loading fresh page...")
                    page.goto(url)
                    page.wait_for_load_state('networkidle')
                    page.wait_for_timeout(1000)
                    
                    # 1-6: 품목 검색
                    self._search_item(page, item)
                    
                    # 7-10: 이 지역에 대한 필터만 적용
                    single_region_filter = DomesticRegionFilter(
                        scope=region_filter.scope,
                        regions=[region]
                    )
                    
                    print(f"  → Created filter with single region: {single_region_filter.regions}")
                    
                    # 다른 필터들도 함께 적용
                    filters_to_apply = [single_region_filter] + other_filters
                    self._apply_filters(page, filters_to_apply)
                    
                    # 11-13: 데이터 다운로드 (파일명에 지역 포함)
                    file_path = self._download_data(page, save_dir, strategy.name, f"{item.name}_{region}")
                    results.append(file_path)
            else:
                # 지역 필터가 없거나 단일 지역인 경우 기존 로직
                url = "https://www.bandtrass.or.kr/customs/total.do?command=CUS001View&viewCode=CUS00301"
                print(f"  [Navigation] Loading fresh page...")
                page.goto(url)
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(1000)
                
                # 1-6: 품목 검색
                self._search_item(page, item)
                
                # 7-10: 필터 적용 및 조회
                if item.filters:
                    print(f"  [Note] Applying {len(item.filters)} filter(s)")
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
        page.locator('div#GODS_DIV').first.click()
        page.wait_for_selector('#GODS_TYPE',  state='visible')
        
        # [2] 드롭다운에서 '품목' 선택
        print(f"  [2] Selecting '품목' from dropdown")
        page.select_option('#GODS_TYPE', value='H')
        page.wait_for_timeout(500)
        
        # [3] '품목 검색하기' 버튼 클릭
        print(f"  [3] Clicking '품목 검색하기'")
        page.locator('span#POPUP1').click()
        
        # 팝업 대기 - 타임아웃 시 대체 처리
        try:
            popup = page.wait_for_event('popup', timeout=10000)
            popup.wait_for_load_state()
            print(f"  → Popup opened")
        except Exception as e:
            print(f"  → Popup timeout: {e}")
            # 팝업이 이미 열려있는지 확인
            contexts = page.context.pages
            if len(contexts) > 1:
                popup = contexts[-1]  # 마지막 페이지가 팝업
                print(f"  → Using existing popup")
            else:
                print(f"  → ERROR: No popup found, retrying...")
                # 다시 클릭 시도
                page.wait_for_timeout(1000)
                page.locator('span#POPUP1').click()
                popup = page.wait_for_event('popup', timeout=10000)
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
        
        # 팝업 닫힘 대기 - 타임아웃 에러 대신 try-except 사용
        try:
            popup.wait_for_event('close', timeout=3000)
            print(f"  → Popup closed successfully")
        except Exception as e:
            print(f"  → Popup close event timeout (expected)")
            # 팝업이 이미 닫혔을 수 있으므로 계속 진행
        
        # 메인 페이지가 준비될 때까지 대기
        print(f"  → Waiting for main page to be ready...")
        page.wait_for_timeout(1000)
        
        # 품목이 선택되었는지 확인 (선택된 품목 표시 영역)
        try:
            # GODS_DIV 영역이 활성화되었는지 확인
            page.wait_for_selector('#GODS_DIV', state='visible', timeout=5000)
            print(f"  → Main page ready, item selected")
        except Exception as e:
            print(f"  → Warning: Could not verify item selection: {e}")
            # 그래도 계속 진행
        
        page.wait_for_timeout(1000)
    
    def _apply_filters(self, page: Page, filters):
        """
        필터 적용 (7-10단계)
        
        Args:
            page: Playwright Page 객체
            filters: 필터 리스트
        """
        for idx, filter in enumerate(filters, 1):
            filter_type_name = type(filter).__name__
            print(f"  [Filter {idx}] Type: {filter_type_name}, Category: {filter.category}")
            print(f"  [Debug] Filter module: {type(filter).__module__}")
            print(f"  [Debug] DomesticRegionFilter module: {DomesticRegionFilter.__module__}")
            print(f"  [Debug] isinstance check: {isinstance(filter, DomesticRegionFilter)}")
            
            # isinstance 체크와 타입 이름 체크 둘 다 시도
            if isinstance(filter, DomesticRegionFilter) or filter_type_name == 'DomesticRegionFilter':
                print(f"  → Matched DomesticRegionFilter")
                self._apply_domestic_region_filter(page, filter)
            elif isinstance(filter, CustomsOfficeFilter) or filter_type_name == 'CustomsOfficeFilter':
                print(f"  → Matched CustomsOfficeFilter")
                self._apply_customs_office_filter(page, filter)
            else:
                print(f"  → ERROR: Unknown filter type!")
    
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
        page.wait_for_timeout(1500)  # dropdown 로드 대기
        
        # [9] 지역 선택 - Bootstrap multiselect 처리
        for region in filter.regions:
            print(f"  [9] Selecting region: '{region}'")
            
            # multiselect 드롭다운 열기 - 더 구체적인 selector 사용
            # LOCATION_DIV 아래의 Select2에 연결된 multiselect 버튼 찾기
            multiselect_button = page.locator('#Select2 + .btn-group button.multiselect')
            
            # 버튼이 보이지 않으면 대체 방법 시도
            if not multiselect_button.count() == 1:
                print(f"  → Trying alternative selector...")
                # FILTER2 (국내지역은 보통 FILTER2)
                multiselect_button = page.locator('#FILTER2_SELECT_CODE button.multiselect').first
            
            multiselect_button.click()
            page.wait_for_timeout(500)
            
            # 검색창에 지역명 입력하여 필터링
            search_input = page.locator('input.multiselect-search').last
            search_input.fill(region)
            page.wait_for_timeout(500)
            
            # 해당 지역의 체크박스 찾기
            # 표시된 항목 중에서만 선택 (multiselect-filter-hidden이 아닌 것)
            checkbox_label = page.locator(f'li:not(.multiselect-filter-hidden) label.checkbox:has-text("{region}")').first
            
            # 체크박스가 이미 체크되어 있는지 확인
            checkbox_input = checkbox_label.locator('input[type="checkbox"]')
            is_checked = checkbox_input.is_checked()
            
            if is_checked:
                print(f"  → Already selected: {region}")
            else:
                checkbox_label.click()
                page.wait_for_timeout(500)
                print(f"  → Selected: {region}")
            
            # 드롭다운 닫기 - 버튼을 다시 클릭해서 토글
            print(f"  → Closing dropdown...")
            multiselect_button.click()
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
        # [7] 세관 필터 선택
        print(f"  [7] Selecting '세관' filter")
        page.locator('div#CSTM_DIV').click()
        # 세관 필터 UI가 렌더링될 때까지 대기
        page.wait_for_timeout(1500)
        
        # [8-9] 세관 선택 - Bootstrap multiselect 처리 (국내지역과 동일한 FILTER2_SELECT_CODE 사용)
        for customs_office in filter.customs_offices:
            print(f"  [8-9] Selecting customs office: '{customs_office}'")
            
            # multiselect 드롭다운 열기 - FILTER2_SELECT_CODE 내의 multiselect 버튼
            multiselect_button = page.locator('#FILTER2_SELECT_CODE button.multiselect').first
            multiselect_button.click()
            page.wait_for_timeout(500)
            
            # 검색창에 세관명 입력하여 필터링
            search_input = page.locator('input.multiselect-search').last
            search_input.fill(customs_office)
            page.wait_for_timeout(500)
            
            # 해당 세관의 체크박스 찾기
            # 표시된 항목 중에서만 선택 (multiselect-filter-hidden이 아닌 것)
            checkbox_label = page.locator(f'li:not(.multiselect-filter-hidden) label.checkbox:has-text("{customs_office}")').first
            
            # 체크박스가 이미 체크되어 있는지 확인
            checkbox_input = checkbox_label.locator('input[type="checkbox"]')
            is_checked = checkbox_input.is_checked()
            
            if is_checked:
                print(f"  → Already selected: {customs_office}")
            else:
                checkbox_label.click()
                page.wait_for_timeout(500)
                print(f"  → Selected: {customs_office}")
            
            # 드롭다운 닫기 - 버튼을 다시 클릭해서 토글
            print(f"  → Closing dropdown...")
            multiselect_button.click()
            page.wait_for_timeout(500)
        
        # [10] 조회하기 버튼 클릭
        print(f"  [10] Clicking '조회하기'")
        page.locator('button[onclick*="goSearch"]').click()
        
        # 결과 테이블 로드 대기
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
        # [11] 첫 번째 행의 수출 금액 셀 클릭 - 팝업 열림
        print(f"  [11] Clicking first row's export amount cell")
        export_amt_cell = page.locator('td[aria-describedby="table_list_1_EX_AMT"] font').first
        export_amt_cell.wait_for()
        
        # 팝업 이벤트 대기 시작
        print(f"  → Waiting for popup to open...")
        try:
            with page.expect_popup(timeout=5000) as popup_info:
                export_amt_cell.click()
            popup = popup_info.value
            popup.wait_for_load_state()
            print(f"  → Popup opened successfully")
        except Exception as e:
            print(f"  → Popup event timeout: {e}")
            # 이미 열린 팝업이 있는지 확인
            contexts = page.context.pages
            if len(contexts) > 1:
                popup = contexts[-1]
                print(f"  → Using existing popup")
            else:
                raise Exception("Failed to open detail popup")
        
        # 팝업 로드 대기 (5초)
        print(f"  → Waiting 5 seconds for popup to fully load...")
        popup.wait_for_timeout(5000)
        
        # 5초 후 팝업 스크린샷 촬영
        screenshot_dir = os.path.join(save_dir, "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshot_dir, f"{strategy_name}_{item_name}_popup.png")
        popup.screenshot(path=screenshot_path)
        print(f"  → Screenshot saved: {screenshot_path}")
        
        # [12] 팝업 내의 다운로드 버튼 클릭
        print(f"  [12] Clicking download button in popup")
        download_btn = popup.locator('a[href*="GridtoExcel"]')
        download_btn.wait_for(state='visible', timeout=10000)
        print(f"  → Download button found!")
        
        # 다운로드 이벤트 리스너 추가 (어디서 발생하는지 확인)
        download_from_popup = []
        download_from_page = []
        
        def on_popup_download(download):
            print(f"  → [EVENT] Download event detected from POPUP!")
            download_from_popup.append(download)
        
        def on_page_download(download):
            print(f"  → [EVENT] Download event detected from MAIN PAGE!")
            download_from_page.append(download)
        
        popup.once('download', on_popup_download)
        page.once('download', on_page_download)
        
        # Dialog 이벤트 리스너 추가 (confirm 대화상자 자동 수락)
        dialog_count = [0]
        def on_dialog(dialog):
            dialog_count[0] += 1
            msg = dialog.message
            dialog_type = dialog.type
            print(f"  → [DIALOG #{dialog_count[0]}] Type: {dialog_type}, Message: {msg[:50]}...")
            try:
                dialog.accept()  # 자동으로 수락
                print(f"  → [DIALOG #{dialog_count[0]}] Accepted")
            except Exception as e:
                # 이미 처리된 dialog는 무시
                print(f"  → [DIALOG #{dialog_count[0]}] Already handled")
        
        popup.on('dialog', on_dialog)
        page.on('dialog', on_dialog)
        
        # 버튼 클릭
        print(f"  → Clicking download button...")
        download_btn.click()
        
        # confirm 대화상자가 나타나고 accept된 후 다운로드가 시작됨
        # 최대 30초간 다운로드 이벤트를 폴링으로 확인
        print(f"  → Waiting for download to start (max 30 seconds)...")
        max_wait = 30  # 최대 30초
        elapsed = 0
        interval = 1  # 1초마다 체크
        
        while elapsed < max_wait:
            if download_from_popup or download_from_page:
                break
            popup.wait_for_timeout(interval * 1000)
            elapsed += interval
            if elapsed % 5 == 0:  # 5초마다 진행 상황 출력
                print(f"  → Still waiting... ({elapsed}s elapsed, {dialog_count[0]} dialogs)")
        
        # 결과 확인
        print(f"  → Total dialogs: {dialog_count[0]}")
        print(f"  → Downloads from popup: {len(download_from_popup)}")
        print(f"  → Downloads from page: {len(download_from_page)}")
        
        # 다운로드 객체 가져오기
        download = None
        if download_from_popup:
            download = download_from_popup[0]
            print(f"  → Using download from popup")
        elif download_from_page:
            download = download_from_page[0]
            print(f"  → Using download from main page")
        else:
            raise Exception(f"No download event triggered after {elapsed} seconds. Dialogs: {dialog_count[0]}")
        
        # [13] 얼럿 자동 수락 (이미 page.on('dialog') 설정됨)
        print(f"  [13] Download accepted")
        
        # 파일 저장
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, f"{strategy_name}_{item_name}.xlsx")
        download.save_as(file_path)
        
        print(f"  → Downloaded: {file_path}")
        
        return file_path
