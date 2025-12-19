import time
import os
from playwright.sync_api import sync_playwright, Page
from domain.ports.scraper_port import ScraperPort
from infra.strategies.dual_filter_strategy import DualFilterStrategy
from infra.strategies.single_filter_strategy import SingleFilterStrategy

class BandtrassScraperAdapter(ScraperPort):
    def __init__(self, headless: bool = True):
        self.headless = headless
        # Credentials could be injected via config/env vars in real app
        self.user_id = "zeya9643"
        self.user_pw = "chlwltjr43!"

    def download_data(self, save_path: str, strategy: dict = None) -> str:
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
                
                # 2. Select Strategy and Execute
                # Currently defaulting to SingleFilterStrategy.
                # In the future, logic can check strategy config to choose MultiFilterStrategy.
                if strategy and 'filter1' in strategy:
                    print("[BandtrassAdapter] Executing DualFilterStrategy...")
                    scraper_strategy = DualFilterStrategy()
                else:
                    print("[BandtrassAdapter] Executing SingleFilterStrategy...")
                    scraper_strategy = SingleFilterStrategy()
                
                final_path = scraper_strategy.execute(page, save_path, strategy)
                
                return final_path
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
