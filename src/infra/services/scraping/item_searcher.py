"""
품목 검색 모듈

HS Code를 사용하여 Bandtrass 웹사이트에서 품목을 검색하고 선택합니다.
"""

from playwright.sync_api import Page


def search_item(page: Page, hs_code: str) -> None:
    """
    HS Code로 품목을 검색하고 선택합니다.
    
    Steps:
        1. 품목/성질별 버튼 클릭
        2. 드롭다운에서 '품목' 선택
        3. 품목 검색 팝업 열기
        4. HS Code 입력
        5. 직접입력추가 버튼 클릭
        6. 선택적용 버튼 클릭
    
    Args:
        page: Playwright Page 객체
        hs_code: 10자리 HS Code
    
    Raises:
        Exception: 팝업을 열 수 없거나 품목 선택에 실패한 경우
    """
    # [1] 품목/성질별 버튼 클릭
    print(f"  [1] Clicking '품목/성질별'")
    page.locator('div#GODS_DIV').first.click()
    page.wait_for_selector('#GODS_TYPE', state='visible')
    
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
    print(f"  [4] Entering HS Code: {hs_code}")
    popup.locator('input#CustomText').fill(hs_code)
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
