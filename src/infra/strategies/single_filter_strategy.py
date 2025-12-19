import time
from playwright.sync_api import Page
from .scraper_strategy import ScraperStrategy

class SingleFilterStrategy(ScraperStrategy):
    def execute(self, page: Page, save_path_dir: str, strategy_config: dict = None) -> str:
        """
        Executes standard search and downloads file to save_path_dir.
        """
        # Config 파싱 (공통 메서드 사용)
        config = self._parse_config(strategy_config)
        hs_code = config['hs_code']
        target_text = config.get('target_text') or "[8504230000] 용량이 10,000킬로볼트암페어를 초과하는 것"
        strategy_name = config['strategy_name']
        
        # URL 이동 (공통 메서드 사용)
        url = "https://www.bandtrass.or.kr/customs/total.do?command=CUS001View&viewCode=CUS00201"
        print(f"[SingleFilterStrategy] Navigating to {url}")
        self._navigate_to_url(page, url)

        # Items 선택
        page.get_by_text("품목/성질별/신성질별").click()
        page.wait_for_selector("#GODS_TYPE", state="visible")
        page.select_option("#GODS_TYPE", value="H")

        # 팝업 처리 (공통 메서드 사용)
        print("[SingleFilterStrategy] Opening Item Search Popup...")
        popup = self._open_item_search_popup(page)
        
        print(f"[SingleFilterStrategy] Searching HS Code: {hs_code}")
        self._search_hs_code_in_popup(popup, hs_code)
        
        self._apply_popup_selection(popup)
        
        # Search 버튼 클릭
        print("[SingleFilterStrategy] Clicking Search Button...")
        try:
             page.click("button[onclick*='goSearch']")
        except:
             page.click("button.btn-ok")

        # 결과 대기 및 상세 셀 찾기
        print(f"[SingleFilterStrategy] Waiting for results and finding detail cell: {target_text}")
        cell_locator = page.get_by_text(target_text)
        cell_locator.wait_for(state="visible", timeout=10000)
        
        # 상세 팝업 열기
        with page.expect_popup() as detail_popup_info:
            cell_locator.click()
        
        detail_popup = detail_popup_info.value
        detail_popup.wait_for_load_state()
        detail_popup.on("dialog", lambda d: d.accept())

        # 다운로드
        print("[SingleFilterStrategy] Clicking GridtoExcel...")
        
        saved_download = None
        try:
            with page.expect_download(timeout=30000) as download_info:
                detail_popup.click("a[href*='GridtoExcel']")
            saved_download = download_info.value
        except Exception:
            print("[SingleFilterStrategy] Checking popup for download event...")
            if not detail_popup.is_closed():
                 with detail_popup.expect_download(timeout=30000) as download_info_popup:
                     detail_popup.click("a[href*='GridtoExcel']")
                 saved_download = download_info_popup.value

        if saved_download:
            print(f"[SingleFilterStrategy] Download Success")
            detail_popup.close()
            
            # 다운로드 저장 및 변환 (공통 메서드 사용)
            return self._save_download(saved_download, save_path_dir, strategy_name)
        else:
            raise Exception("Download failed in SingleFilterStrategy")
