import time
import os
import pandas as pd
from playwright.sync_api import Page
from .scraper_strategy import ScraperStrategy

class SingleFilterStrategy(ScraperStrategy):
    def execute(self, page: Page, save_path_dir: str, strategy_config: dict = None) -> str:
        """
        Executes standard search and downloads file to save_path_dir.
        """
        # Default Strategy
        hs_code = "8504230000"
        target_text = "[8504230000] 용량이 10,000킬로볼트암페어를 초과하는 것"
        strategy_name = ""
        
        if strategy_config and 'search' in strategy_config:
            hs_code = strategy_config['search'].get('hs_code', hs_code)
            target_text = strategy_config['search'].get('target_text', target_text)
            if 'name' in strategy_config:
                strategy_name = f"_{strategy_config['name']}"

        # Search URL
        url = "https://www.bandtrass.or.kr/customs/total.do?command=CUS001View&viewCode=CUS00201"
        print(f"[SingleFilterStrategy] Navigating to {url}")
        page.goto(url)
        page.wait_for_load_state('networkidle')

        # Items
        page.get_by_text("품목/성질별/신성질별").click()
        page.wait_for_selector("#GODS_TYPE", state="visible")
        page.select_option("#GODS_TYPE", value="H")

        # Popup - Search Item
        print("[SingleFilterStrategy] Opening Item Search Popup...")
        page.wait_for_selector("#POPUP1", state="visible")
        with page.expect_popup() as popup_info:
            page.click("#POPUP1")
        
        popup = popup_info.value
        popup.wait_for_load_state()

        # Input Code
        print(f"[SingleFilterStrategy] Searching HS Code: {hs_code}")
        popup.wait_for_selector("#CustomText")
        popup.fill("#CustomText", hs_code)
        popup.click("#CustomCheck")
        time.sleep(0.5)

        # Apply
        try:
            with popup.expect_event("close"):
                popup.get_by_text("선택적용", exact=True).click()
        except:
            if not popup.is_closed():
                popup.get_by_text("선택적용", exact=True).click()
        
        # Search
        print("[SingleFilterStrategy] Clicking Search Button...")
        try:
             page.click("button[onclick*='goSearch']")
        except:
             page.click("button.btn-ok")

        # Wait for Grid and Find Detail Cell
        print(f"[SingleFilterStrategy] Waiting for results and finding detail cell: {target_text}")
        cell_locator = page.get_by_text(target_text)
        cell_locator.wait_for(state="visible", timeout=10000)
        
        # Open Detail Popup
        with page.expect_popup() as detail_popup_info:
            cell_locator.click()
        
        detail_popup = detail_popup_info.value
        detail_popup.wait_for_load_state()
        
        # Attach dialog listener (handled by adapter context usually, but good to ensure)
        # Assuming adapter attached global listener, but valid to attach here if specific to popup persistence
        # For now, we rely on the clean structure. Context (Adapter) handles browser-wide events if possible,
        # but popup new pages might need re-attachment. 
        # Ideally, we pass a callback or specific handler if needed.
        # Let's attach a simple acceptor to be safe, or assume the main page listener covers if contexts match.
        detail_popup.on("dialog", lambda d: d.accept())

        # Download
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
            timestamp = int(time.time())
            filename_xls = f"bandtrass_{timestamp}{strategy_name}.xls"
            full_path_xls = os.path.join(save_path_dir, filename_xls)
            saved_download.save_as(full_path_xls)
            print(f"[SingleFilterStrategy] Download Success: {full_path_xls}")
            detail_popup.close()
            
            # Conversion
            try:
                print("[SingleFilterStrategy] Converting XLS to XLSX...")
                # Note: 'pd' imported at top
                df = pd.read_excel(full_path_xls)
                
                filename_xlsx = f"bandtrass_{timestamp}.xlsx"
                full_path_xlsx = os.path.join(save_path_dir, filename_xlsx)
                
                df.to_excel(full_path_xlsx, index=False)
                print(f"[SingleFilterStrategy] Saved as: {full_path_xlsx}")
                os.remove(full_path_xls)
                
                return full_path_xlsx
                
            except Exception as e:
                print(f"[SingleFilterStrategy] Conversion Failed: {e}")
                return full_path_xls
        else:
            raise Exception("Download failed in SingleFilterStrategy")
