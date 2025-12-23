"""
필터 적용 모듈

국내지역, 세관 등 다양한 필터를 Bandtrass 웹사이트에 적용합니다.
"""

from playwright.sync_api import Page


def apply_filters(page: Page, filters: list) -> None:
    """
    필터 리스트를 순회하며 각 필터를 적용합니다.
    
    Args:
        page: Playwright Page 객체
        filters: 적용할 필터 객체 리스트 (DomesticRegionFilter, CustomsOfficeFilter 등)
    """
    for idx, filter_obj in enumerate(filters, 1):
        filter_type_name = type(filter_obj).__name__
        print(f"  [Filter {idx}] Type: {filter_type_name}, Category: {filter_obj.category}")
        
        # 타입 이름으로 체크 (isinstance는 모듈 경로 차이로 실패할 수 있음)
        if filter_type_name == 'DomesticRegionFilter':
            print(f"  → Matched DomesticRegionFilter")
            apply_domestic_region_filter(page, filter_obj.scope, filter_obj.regions)
        elif filter_type_name == 'CustomsOfficeFilter':
            print(f"  → Matched CustomsOfficeFilter")
            apply_customs_office_filter(page, filter_obj.customs_offices)
        else:
            print(f"  → ERROR: Unknown filter type!")


def apply_domestic_region_filter(page: Page, scope: str, regions: list[str]) -> None:
    """
    국내지역 필터를 적용합니다.
    
    Args:
        page: Playwright Page 객체
        scope: 지역 범위 ('시' 또는 '시군구')
        regions: 선택할 지역명 리스트
    """
    # [7] 국내지역 필터 선택
    print(f"  [7] Selecting '국내지역' filter")
    page.locator('div#LOCATION_DIV').click()
    page.wait_for_selector('#LOCATION_TYPE', state='visible')
    
    # [8] Scope 선택 (시, 시군구, etc.)
    print(f"  [8] Selecting scope: '{scope}'")
    scope_value = {'시': 'A', '시군구': 'B'}.get(scope, 'A')
    page.select_option('#LOCATION_TYPE', value=scope_value)
    page.wait_for_timeout(1500)  # dropdown 로드 대기
    
    # [9] 지역 선택 - Bootstrap multiselect 처리
    for region in regions:
        print(f"  [9] Selecting region: '{region}'")
        
        # multiselect 드롭다운 열기 - 더 구체적인 selector 사용
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
        
        # 드롭다운 닫기
        print(f"  → Closing dropdown...")
        multiselect_button.click()
        page.wait_for_timeout(500)
    
    # [10] 조회하기 버튼 클릭
    print(f"  [10] Clicking '조회하기'")
    page.locator('button[onclick*="goSearch"]').click()
    
    # 결과 테이블 로드 대기
    page.wait_for_selector('#table_list_1 tr.jqgrow', timeout=10000)
    page.wait_for_timeout(2000)


def apply_customs_office_filter(page: Page, customs_offices: list[str]) -> None:
    """
    세관 필터를 적용합니다.
    
    Args:
        page: Playwright Page 객체
        customs_offices: 선택할 세관명 리스트
    """
    # [7] 세관 필터 선택
    print(f"  [7] Selecting '세관' filter")
    page.locator('div#CSTM_DIV').click()
    # 세관 필터 UI가 렌더링될 때까지 대기
    page.wait_for_timeout(1500)
    
    # [8-9] 세관 선택 - Bootstrap multiselect 처리
    for customs_office in customs_offices:
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
        
        # 드롭다운 닫기
        print(f"  → Closing dropdown...")
        multiselect_button.click()
        page.wait_for_timeout(500)
    
    # [10] 조회하기 버튼 클릭
    print(f"  [10] Clicking '조회하기'")
    page.locator('button[onclick*="goSearch"]').click()
    
    # 결과 테이블 로드 대기
    page.wait_for_selector('#table_list_1 tr.jqgrow', timeout=10000)
    page.wait_for_timeout(2000)
