"""
데이터 다운로드 모듈

조회 결과에서 상세 데이터를 다운로드하여 Excel 파일로 저장합니다.
"""

import os
from playwright.sync_api import Page


def download_data(page: Page, save_dir: str, filename: str) -> str:
    """
    조회 결과에서 데이터를 다운로드하여 Excel 파일로 저장합니다.
    
    Steps:
        11. 수출 금액 셀 클릭 → 상세 팝업 열기
        12. 팝업에서 다운로드 버튼 클릭
        13. Excel 파일로 저장
    
    Args:
        page: Playwright Page 객체
        save_dir: 저장 디렉토리 경로
        filename: 저장할 파일명 (확장자 제외)
    
    Returns:
        다운로드된 파일의 전체 경로
    
    Raises:
        Exception: 팝업을 열 수 없거나 다운로드에 실패한 경우
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
    
    # 스크린샷 촬영
    screenshot_dir = os.path.join(save_dir, "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_path = os.path.join(screenshot_dir, f"{filename}_popup.png")
    popup.screenshot(path=screenshot_path)
    print(f"  → Screenshot saved: {screenshot_path}")
    
    # [12] 팝업 내의 다운로드 버튼 클릭
    print(f"  [12] Clicking download button in popup")
    download_btn = popup.locator('a[href*="GridtoExcel"]')
    download_btn.wait_for(state='visible', timeout=10000)
    print(f"  → Download button found!")
    
    # 다운로드 이벤트 리스너 추가
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
            dialog.accept()
            print(f"  → [DIALOG #{dialog_count[0]}] Accepted")
        except Exception as e:
            print(f"  → [DIALOG #{dialog_count[0]}] Already handled")
    
    popup.on('dialog', on_dialog)
    page.on('dialog', on_dialog)
    
    # 버튼 클릭
    print(f"  → Clicking download button...")
    download_btn.click()
    
    # 다운로드 이벤트 대기 (최대 30초)
    print(f"  → Waiting for download to start (max 30 seconds)...")
    max_wait = 30
    elapsed = 0
    interval = 1
    
    while elapsed < max_wait:
        if download_from_popup or download_from_page:
            break
        popup.wait_for_timeout(interval * 1000)
        elapsed += interval
        if elapsed % 5 == 0:
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
    
    # [13] 파일 저장
    print(f"  [13] Download accepted")
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, f"{filename}.xlsx")
    download.save_as(file_path)
    
    print(f"  → Downloaded: {file_path}")
    
    return file_path
