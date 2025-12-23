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
        filters: 적용할 필터 객체 리스트
    """
    for idx, filter_obj in enumerate(filters, 1):
        filter_type_name = type(filter_obj).__name__
        print(f"  [Filter {idx}] Type: {filter_type_name}, Category: {filter_obj.category}")
        
        if filter_type_name == 'DomesticRegionFilter':
            print("  → Matched DomesticRegionFilter")
            apply_domestic_region_filter(page, filter_obj.scope, filter_obj.regions)
        elif filter_type_name == 'CustomsOfficeFilter':
            print("  → Matched CustomsOfficeFilter")
            apply_customs_office_filter(page, filter_obj.customs_offices)
        else:
            print("  → ERROR: Unknown filter type!")


def apply_domestic_region_filter(page: Page, scope: str, regions: list[str]) -> None:
    """
    국내지역 필터를 적용합니다.
    
    Args:
        page: Playwright Page 객체
        scope: 지역 범위 ('시' 또는 '시군구')
        regions: 선택할 지역명 리스트
    """
    _select_location_filter(page)
    _select_location_scope(page, scope)
    
    for region in regions:
        _select_region_item(page, region)
    
    _submit_search_query(page)


def apply_customs_office_filter(page: Page, customs_offices: list[str]) -> None:
    """
    세관 필터를 적용합니다.
    
    Args:
        page: Playwright Page 객체
        customs_offices: 선택할 세관명 리스트
    """
    _select_customs_filter(page)
    
    for customs_office in customs_offices:
        _select_customs_item(page, customs_office)
    
    _submit_search_query(page)


def _select_location_filter(page: Page) -> None:
    """국내지역 필터 버튼을 클릭합니다."""
    print("  [7] Selecting '국내지역' filter")
    page.locator('div#LOCATION_DIV').click()
    page.wait_for_selector('#LOCATION_TYPE', state='visible')


def _select_location_scope(page: Page, scope: str) -> None:
    """지역 범위를 선택합니다."""
    print(f"  [8] Selecting scope: '{scope}'")
    scope_value = {'시': 'A', '시군구': 'B'}.get(scope, 'A')
    page.select_option('#LOCATION_TYPE', value=scope_value)
    page.wait_for_timeout(1500)


def _select_region_item(page: Page, region: str) -> None:
    """특정 지역을 선택합니다."""
    print(f"  [9] Selecting region: '{region}'")
    multiselect_button = _get_multiselect_button(page)
    _open_dropdown(multiselect_button, page)
    _search_and_select_item(page, region)
    _close_dropdown(multiselect_button, page)


def _select_customs_filter(page: Page) -> None:
    """세관 필터 버튼을 클릭합니다."""
    print("  [7] Selecting '세관' filter")
    page.locator('div#CSTM_DIV').click()
    page.wait_for_timeout(1500)


def _select_customs_item(page: Page, customs_office: str) -> None:
    """특정 세관을 선택합니다."""
    print(f"  [8-9] Selecting customs office: '{customs_office}'")
    multiselect_button = page.locator('#FILTER2_SELECT_CODE button.multiselect').first
    _open_dropdown(multiselect_button, page)
    _search_and_select_item(page, customs_office)
    _close_dropdown(multiselect_button, page)


def _get_multiselect_button(page: Page):
    """multiselect 버튼을 반환합니다."""
    multiselect_button = page.locator('#Select2 + .btn-group button.multiselect')
    
    if not multiselect_button.count() == 1:
        print("  → Trying alternative selector...")
        return page.locator('#FILTER2_SELECT_CODE button.multiselect').first
    
    return multiselect_button


def _open_dropdown(button, page: Page) -> None:
    """드롭다운을 엽니다."""
    button.click()
    page.wait_for_timeout(500)


def _close_dropdown(button, page: Page) -> None:
    """드롭다운을 닫습니다."""
    print("  → Closing dropdown...")
    button.click()
    page.wait_for_timeout(500)


def _search_and_select_item(page: Page, item_name: str) -> None:
    """검색창에서 항목을 검색하고 선택합니다."""
    search_input = page.locator('input.multiselect-search').last
    search_input.fill(item_name)
    page.wait_for_timeout(500)
    
    checkbox_label = page.locator(
        f'li:not(.multiselect-filter-hidden) label.checkbox:has-text("{item_name}")'
    ).first
    
    if _is_checkbox_checked(checkbox_label):
        print(f"  → Already selected: {item_name}")
    else:
        checkbox_label.click()
        page.wait_for_timeout(500)
        print(f"  → Selected: {item_name}")


def _is_checkbox_checked(checkbox_label) -> bool:
    """체크박스가 선택되어 있는지 확인합니다."""
    checkbox_input = checkbox_label.locator('input[type="checkbox"]')
    return checkbox_input.is_checked()


def _submit_search_query(page: Page) -> None:
    """조회하기 버튼을 클릭하고 결과를 대기합니다."""
    print("  [10] Clicking '조회하기'")
    page.locator('button[onclick*="goSearch"]').click()
    page.wait_for_selector('#table_list_1 tr.jqgrow', timeout=10000)
    page.wait_for_timeout(2000)
