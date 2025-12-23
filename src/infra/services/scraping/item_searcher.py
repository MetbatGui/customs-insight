"""
품목 검색 모듈

HS Code를 사용하여 Bandtrass 웹사이트에서 품목을 검색하고 선택합니다.
"""

from playwright.sync_api import Page


def search_item(page: Page, hs_code: str) -> None:
    """
    HS Code로 품목을 검색하고 선택합니다.
    
    Args:
        page: Playwright Page 객체
        hs_code: 10자리 HS Code
    
    Raises:
        Exception: 팝업을 열 수 없거나 품목 선택에 실패한 경우
    """
    _click_item_category_button(page)
    _select_item_from_dropdown(page)
    _click_item_search_button(page)
    popup = _get_search_popup(page)
    _fill_hs_code(popup, hs_code)
    _click_add_button(popup)
    _click_apply_button(popup)
    _wait_for_popup_close(popup)
    _wait_for_main_page_ready(page)


def _click_item_category_button(page: Page) -> None:
    """품목/성질별 버튼을 클릭합니다."""
    print("  [1] Clicking '품목/성질별'")
    page.locator('div#GODS_DIV').first.click()
    page.wait_for_selector('#GODS_TYPE', state='visible')


def _select_item_from_dropdown(page: Page) -> None:
    """드롭다운에서 '품목'을 선택합니다."""
    print("  [2] Selecting '품목' from dropdown")
    page.select_option('#GODS_TYPE', value='H')
    page.wait_for_timeout(500)


def _click_item_search_button(page: Page) -> None:
    """품목 검색하기 버튼을 클릭합니다."""
    print("  [3] Clicking '품목 검색하기'")
    page.locator('span#POPUP1').click()


def _get_search_popup(page: Page) -> Page:
    """
    품목 검색 팝업을 반환합니다.
    
    타임아웃 시 기존 팝업을 사용하거나 재시도합니다.
    
    Returns:
        품목 검색 팝업 Page 객체
    """
    try:
        popup = page.wait_for_event('popup', timeout=10000)
        popup.wait_for_load_state()
        print("  → Popup opened")
        return popup
    except Exception as e:
        print(f"  → Popup timeout: {e}")
        return _handle_popup_timeout(page)


def _handle_popup_timeout(page: Page) -> Page:
    """팝업 타임아웃 시 대체 처리를 수행합니다."""
    contexts = page.context.pages
    if len(contexts) > 1:
        print("  → Using existing popup")
        return contexts[-1]
    
    print("  → ERROR: No popup found, retrying...")
    page.wait_for_timeout(1000)
    page.locator('span#POPUP1').click()
    popup = page.wait_for_event('popup', timeout=10000)
    popup.wait_for_load_state()
    return popup


def _fill_hs_code(popup: Page, hs_code: str) -> None:
    """HS Code를 입력합니다."""
    print(f"  [4] Entering HS Code: {hs_code}")
    popup.locator('input#CustomText').fill(hs_code)
    popup.wait_for_timeout(500)


def _click_add_button(popup: Page) -> None:
    """직접입력추가 버튼을 클릭합니다."""
    print("  [5] Clicking '직접입력추가'")
    popup.locator('button#CustomCheck').click()
    popup.wait_for_timeout(1000)


def _click_apply_button(popup: Page) -> None:
    """선택적용 버튼을 클릭합니다."""
    print("  [6] Clicking '선택적용'")
    popup.locator('button[onclick="fn_ok();"]').click()


def _wait_for_popup_close(popup: Page) -> None:
    """팝업이 닫힐 때까지 대기합니다."""
    try:
        popup.wait_for_event('close', timeout=3000)
        print("  → Popup closed successfully")
    except Exception:
        print("  → Popup close event timeout (expected)")


def _wait_for_main_page_ready(page: Page) -> None:
    """메인 페이지가 준비될 때까지 대기합니다."""
    print("  → Waiting for main page to be ready...")
    page.wait_for_timeout(1000)
    
    try:
        page.wait_for_selector('#GODS_DIV', state='visible', timeout=5000)
        print("  → Main page ready, item selected")
    except Exception as e:
        print(f"  → Warning: Could not verify item selection: {e}")
    
    page.wait_for_timeout(1000)
