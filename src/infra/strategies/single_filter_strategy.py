import time
from playwright.sync_api import Page
from .scraper_strategy import ScraperStrategy


class SingleFilterStrategy(ScraperStrategy):
    """단일 필터 기반 스크래핑 전략입니다.
    
    이 전략은 HS Code로 품목을 검색하고 해당 품목의 상세 데이터를
    다운로드합니다. 품목/성질별 검색 페이지를 사용합니다.
    
    주요 동작:
        1. 품목/성질별 검색 페이지로 이동
        2. HS Code 입력 (팝업 사용)
        3. 검색 실행
        4. 상세 데이터 팝업 열기
        5. Excel 다운로드 및 변환
    
    Examples:
        >>> strategy = SingleFilterStrategy()
        >>> file_path = strategy.execute(page, "data", config)
    """
    
    def execute(self, page: Page, save_path_dir: str, strategy_config: dict = None) -> str:
        """표준 검색을 실행하고 파일을 다운로드합니다.
        
        HS Code를 사용하여 품목을 검색하고, 검색 결과에서 상세 데이터를
        다운로드하여 지정된 디렉토리에 저장합니다.
        
        Args:
            page: 이미 로그인된 Playwright Page 객체.
            save_path_dir: 파일을 저장할 디렉토리 경로.
            strategy_config: Strategy 설정 딕셔너리. 다음을 포함할 수 있음:
                - search.hs_code: 검색할 HS Code
                - search.target_text: 검색 결과에서 찾을 텍스트
                - name: Strategy 이름
        
        Returns:
            다운로드된 XLSX 파일의 전체 경로.
        
        Raises:
            Exception: 다운로드 실패 시.
        
        Examples:
            >>> config = {
            ...     'search': {'hs_code': '8504230000'},
            ...     'name': '삼양'
            ... }
            >>> result = strategy.execute(page, "data", config)
            >>> print(result)
            data/bandtrass_1234567890_삼양.xl sx
        """
        config = self._parse_config(strategy_config)
        hs_code = config['hs_code']
        target_text = config.get('target_text') or "[8504230000] 용량이 10,000킬로볼트암페어를 초과하는 것"
        strategy_name = config['strategy_name']
        
        url = "https://www.bandtrass.or.kr/customs/total.do?command=CUS001View&viewCode=CUS00201"
        print(f"[SingleFilterStrategy] Navigating to {url}")
        self._navigate_to_url(page, url)

        page.get_by_text("품목/성질별/신성질별").click()
        page.wait_for_selector("#GODS_TYPE", state="visible")
        page.select_option("#GODS_TYPE", value="H")

        print("[SingleFilterStrategy] Opening Item Search Popup...")
        popup = self._open_item_search_popup(page)
        
        print(f"[SingleFilterStrategy] Searching HS Code: {hs_code}")
        self._search_hs_code_in_popup(popup, hs_code)
        
        self._apply_popup_selection(popup)
        
        print("[SingleFilterStrategy] Clicking Search Button...")
        try:
             page.click("button[onclick*='goSearch']")
        except:
             page.click("button.btn-ok")

        print(f"[SingleFilterStrategy] Waiting for results and finding detail cell: {target_text}")
        cell_locator = page.get_by_text(target_text)
        cell_locator.wait_for(state="visible", timeout=10000)
        
        with page.expect_popup() as detail_popup_info:
            cell_locator.click()
        
        detail_popup = detail_popup_info.value
        detail_popup.wait_for_load_state()
        detail_popup.on("dialog", lambda d: d.accept())

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
            
            return self._save_download(saved_download, save_path_dir, strategy_name)
        else:
            raise Exception("Download failed in SingleFilterStrategy")
