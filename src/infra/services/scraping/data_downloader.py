"""
데이터 다운로드 모듈

조회 결과에서 상세 데이터를 다운로드하여 Excel 파일로 저장합니다.
"""

import os
from playwright.sync_api import Page


def download_data(page: Page, save_dir: str, filename: str) -> str:
    """
    조회 결과에서 데이터를 다운로드하여 Excel 파일로 저장합니다.
    
    Args:
        page: Playwright Page 객체
        save_dir: 저장 디렉토리 경로
        filename: 저장할 파일명 (확장자 제외)
    
    Returns:
        다운로드된 파일의 전체 경로
    
    Raises:
        Exception: 팝업을 열 수 없거나 다운로드에 실패한 경우
    """
    popup = _open_detail_popup(page)
    _wait_and_save_screenshot(popup, save_dir, filename)
    download = _trigger_download_with_listeners(popup, page)
    return _save_download_file(download, save_dir, filename)


def _open_detail_popup(page: Page) -> Page:
    """첫 번째 행의 수출 금액 셀을 클릭하여 상세 팝업을 엽니다."""
    print("  [11] Clicking first row's export amount cell")
    export_amt_cell = page.locator('td[aria-describedby="table_list_1_EX_AMT"] font').first
    export_amt_cell.wait_for()
    
    print("  → Waiting for popup to open...")
    try:
        with page.expect_popup(timeout=5000) as popup_info:
            export_amt_cell.click()
        popup = popup_info.value
        popup.wait_for_load_state()
        print("  → Popup opened successfully")
        return popup
    except Exception as e:
        print(f"  → Popup event timeout: {e}")
        return _get_existing_popup(page)


def _get_existing_popup(page: Page) -> Page:
    """이미 열려있는 팝업을 찾아 반환합니다."""
    contexts = page.context.pages
    if len(contexts) > 1:
        print("  → Using existing popup")
        return contexts[-1]
    raise Exception("Failed to open detail popup")


def _wait_and_save_screenshot(popup: Page, save_dir: str, filename: str) -> None:
    """팝업 로드를 대기하고 스크린샷을 저장합니다."""
    print("  → Waiting 5 seconds for popup to fully load...")
    popup.wait_for_timeout(5000)
    
    screenshot_dir = os.path.join(save_dir, "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_path = os.path.join(screenshot_dir, f"{filename}_popup.png")
    popup.screenshot(path=screenshot_path)
    print(f"  → Screenshot saved: {screenshot_path}")


def _trigger_download_with_listeners(popup: Page, page: Page):
    """다운로드 버튼을 클릭하고 다운로드 이벤트를 대기합니다."""
    download_btn = _find_download_button(popup)
    download_lists = _setup_download_listeners(popup, page)
    dialog_count = _setup_dialog_listener(popup, page)
    
    _click_download_button(download_btn)
    _wait_for_download_start(popup, download_lists['popup'], download_lists['page'], dialog_count)
    
    return _get_download_object(download_lists['popup'], download_lists['page'], dialog_count[0])


def _find_download_button(popup: Page):
    """다운로드 버튼을 찾습니다."""
    print("  [12] Clicking download button in popup")
    download_btn = popup.locator('a[href*="GridtoExcel"]')
    download_btn.wait_for(state='visible', timeout=10000)
    print("  → Download button found!")
    return download_btn


def _setup_download_listeners(popup: Page, page: Page) -> dict:
    """다운로드 이벤트 리스너를 설정합니다."""
    download_from_popup = []
    download_from_page = []
    
    popup.once('download', lambda d: (
        print("  → [EVENT] Download event detected from POPUP!"),
        download_from_popup.append(d)
    ))
    page.once('download', lambda d: (
        print("  → [EVENT] Download event detected from MAIN PAGE!"),
        download_from_page.append(d)
    ))
    
    return {'popup': download_from_popup, 'page': download_from_page}


def _setup_dialog_listener(popup: Page, page: Page) -> list:
    """Dialog 이벤트 리스너를 설정합니다."""
    dialog_count = [0]
    
    def on_dialog(dialog):
        dialog_count[0] += 1
        msg = dialog.message
        dialog_type = dialog.type
        print(f"  → [DIALOG #{dialog_count[0]}] Type: {dialog_type}, Message: {msg[:50]}...")
        try:
            dialog.accept()
            print(f"  → [DIALOG #{dialog_count[0]}] Accepted")
        except Exception:
            print(f"  → [DIALOG #{dialog_count[0]}] Already handled")
    
    popup.on('dialog', on_dialog)
    page.on('dialog', on_dialog)
    return dialog_count


def _click_download_button(download_btn) -> None:
    """다운로드 버튼을 클릭합니다."""
    print("  → Clicking download button...")
    download_btn.click()


def _wait_for_download_start(popup: Page, downloads_popup: list, downloads_page: list, dialog_count: list) -> None:
    """다운로드가 시작될 때까지 대기합니다."""
    print("  → Waiting for download to start (max 30 seconds)...")
    max_wait = 30
    elapsed = 0
    
    while elapsed < max_wait:
        if downloads_popup or downloads_page:
            break
        popup.wait_for_timeout(1000)
        elapsed += 1
        if elapsed % 5 == 0:
            print(f"  → Still waiting... ({elapsed}s elapsed, {dialog_count[0]} dialogs)")


def _get_download_object(downloads_popup: list, downloads_page: list, dialog_count: int):
    """다운로드 객체를 반환합니다."""
    print(f"  → Total dialogs: {dialog_count}")
    print(f"  → Downloads from popup: {len(downloads_popup)}")
    print(f"  → Downloads from page: {len(downloads_page)}")
    
    if downloads_popup:
        print("  → Using download from popup")
        return downloads_popup[0]
    elif downloads_page:
        print("  → Using download from main page")
        return downloads_page[0]
    else:
        raise Exception(f"No download event triggered. Dialogs: {dialog_count}")


def _save_download_file(download, save_dir: str, filename: str) -> str:
    """다운로드된 파일을 저장합니다."""
    print("  [13] Download accepted")
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, f"{filename}.xlsx")
    download.save_as(file_path)
    print(f"  → Downloaded: {file_path}")
    return file_path
