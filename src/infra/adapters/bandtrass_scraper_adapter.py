import time
import os
from playwright.sync_api import sync_playwright, Page
from src.domain.ports.scraper_port import ScraperPort
from src.domain.models import Strategy
from src.infra.services.strategy_executor import StrategyExecutor


class BandtrassScraperAdapter(ScraperPort):
    """
    Bandtrass 스크래퍼 어댑터
    
    Strategy TOML 파일을 로드하여 StrategyExecutor로 실행합니다.
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        # Credentials could be injected via config/env vars in real app
        self.user_id = "zeya9643"
        self.user_pw = "chlwltjr43!"

    def download_data(self, save_path: str, strategy_path: str = None) -> list[str]:
        """
        데이터 다운로드
        
        Args:
            save_path: 저장 디렉토리
            strategy_path: Strategy TOML 파일 경로
            
        Returns:
            다운로드된 파일 경로 리스트
        """
        with sync_playwright() as p:
            print("[BandtrassAdapter] Launching browser...")
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()

            # Handle Dialogs globally for this page
            page.on("dialog", self._handle_dialog)

            try:
                # 1. Login
                self._login(page)
                
                # 2. Load Strategy
                if strategy_path:
                    print(f"[BandtrassAdapter] Loading strategy from: {strategy_path}")
                    strategy = Strategy.from_toml_file(strategy_path)
                else:
                    raise ValueError("strategy_path is required")
                
                # 3. Execute Strategy using StrategyExecutor
                print(f"[BandtrassAdapter] Executing strategy: {strategy.name}")
                executor = StrategyExecutor()
                results = executor.execute(page, save_path, strategy)
                
                return results
            finally:
                context.close()
                browser.close()
                print("[BandtrassAdapter] Browser closed.")

    def _handle_dialog(self, dialog):
        print(f"[Dialog Detected] {dialog.message}")
        try:
            dialog.accept()
        except Exception:
            pass

    def _login(self, page: Page):
        url = "https://www.bandtrass.or.kr/login.do?command=loginFormLocalID&endPoint=%2Flogin.do%3Fcommand%3DloginAnyIDForm%26returnPage%3DM"
        print(f"[Login] Navigating to {url}")
        page.goto(url)
        page.wait_for_load_state('networkidle')

        print("[Login] Entering credentials...")
        page.fill("#id", self.user_id)
        page.fill("#pw", self.user_pw)

        print("[Login] Clicking Login button...")
        try:
            page.click("button[onclick*=\"Login('1')\"]")
        except Exception:
            page.get_by_text("아이디로 로그인").click()
        
        # Wait for login processing
        print("[Login] Waiting 3 seconds...")
        time.sleep(3)
