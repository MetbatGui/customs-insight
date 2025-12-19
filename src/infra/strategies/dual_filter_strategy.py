import time
import os
import pandas as pd
from playwright.sync_api import Page
from .scraper_strategy import ScraperStrategy

class DualFilterStrategy(ScraperStrategy):
    """이중 필터 기반 스크래핑 전략입니다.
    
    이 전략은 HS Code로 품목을 검색한 후, 여러 지역(필터)에 대해
    반복적으로 데이터를 다운로드하고 병합합니다.
    
    주요 동작:
        1. 지역별 검색 페이지로 이동
        2. HS Code 및 지역 설정
        3. 각 지역별로 반복:
           - 지역 셀 클릭
           - 상세 데이터 다운로드
        4. 모든 파일 병합
        5. Reports 디렉토리에 통합 리포트 저장
    
    Examples:
        >>> config = {
        ...     'search': {'hs code': '8504230000'},
        ...     'filter1': {'type': 'sido', 'data': ['부산', '경남']},
        ...     'name': '삼양'
        ... }
        >>> strategy = DualFilterStrategy()
        >>> report_path = strategy.execute(page, "data", config)
    """
    
    def execute(self, page: Page, save_path_dir: str, strategy_config: dict = None) -> str:
        """이중 필터 검색을 실행하고 통합 리포트를 생성합니다.
        
        여러 지역에 대해 반복적으로 데이터를 다운로드하고,
        모든 데이터를 병합하여 하나의 리포트 파일로 생성합니다.
        
        Args:
            page: 이미 로그인된 Playwright Page 객체.
            save_path_dir: 임시 파일을 저장할 디렉토리 (자동 삭제됨).
            strategy_config: Strategy 설정 딕셔너리. 다음을 포함해야 함:
                - search.hs_code: 검색할 HS Code
                - filter1.type: 필터 타입 (예: "sido")
                - filter1.data: 지역 리스트 (예: ["부산", "경남"])
                - name: Strategy 이름
        
        Returns:
            생성된 통합 리포트 파일의 전체 경로 (reports/ 디렉토리).
            실패 시 빈 문자열.
        
        Note:
            - 임시 다운로드 파일은 병합 후 자동으로 삭제됩니다.
            - 최종 리포트는 DataProcessor로 처리되어 MoM/YoY가 포함됩니다.
        """
        print("[DualFilterStrategy] Strategy Config:", strategy_config)
        
        # 1. Config Extraction (공통 메서드 사용)
        config = self._parse_config(strategy_config)
        hs_code = config['hs_code']
        target_text = config.get('target_text', "")
        strategy_name = config['strategy_name'] or strategy_config.get('name', 'std')

        filter1 = strategy_config.get('filter1', {})
        filter_type = filter1.get('type') # e.g., "sido"
        filter_data_list = filter1.get('data', []) # e.g., ["부산", "경남"]

        if not filter_data_list:
            print("[DualFilterStrategy] No filter data found. Aborting.")
            return ""

        # 2. Navigation (공통 메서드 사용)
        url = "https://www.bandtrass.or.kr/customs/total.do?command=CUS001View&viewCode=CUS00301"
        print(f"[DualFilterStrategy] Navigating to {url}")
        self._navigate_to_url(page, url)

        # 3. Setup Basic Search Conditions
        # Select "Import/Export Results by Item" (CUS00301 pattern)
        # We assume the user wants to search for a specific item across ALL regions.

        # A. Select Item Type (HS Code)
        try:
            # Note: Selectors need to be verified for the specific page
            page.get_by_text("품목/성질별/신성질별").click()
            page.wait_for_selector("#GODS_TYPE", state="visible")
            page.select_option("#GODS_TYPE", value="H") # HS Code
        except Exception as e:
            print(f"[DualFilterStrategy] Item type selection warning: {e}")

        # B. Input HS Code
        print(f"[DualFilterStrategy] Searching HS Code: {hs_code}")
        try:
            # Assuming direct input is possible or via popup
            # For this flow, we'll assume we can enter it or use text search
            # If popup is needed:
            # page.click("#POPUP_BTN") ...
            # For now, simplistic approach:
             page.fill("input[name='HS_CD']", hs_code) 
        except:
            print("[DualFilterStrategy] Could not fill HS Code directly, trying popup flow...")
            
            # Popup Logic (Adapted from SingleFilterStrategy)
            try:
                # 1. Open Popup (공통 메서드 사용)
                popup = self._open_item_search_popup(page)

                # 2. Input Code into #CustomText
                popup.wait_for_selector("#CustomText")
                popup.fill("#CustomText", hs_code)
                print(f"[DualFilterStrategy] Filled HS Code {hs_code} into popup.")

                # 3. Click 'Direct Input Add' (직접입력추가)
                # User provided snippet: <button ... onclick="CustomAdd();" ...>직접입력추가</button>
                # This adds the code directly without searching the grid.
                try:
                    popup.get_by_text("직접입력추가").click()
                    print("[DualFilterStrategy] Clicked 'Direct Input Add' button.")
                    time.sleep(1) # Wait for row to appear
                
                except Exception as e:
                    print(f"[DualFilterStrategy] Direct Add failed: {e}")
                    # Fallback ID click
                    popup.click("#CustomCheck")

                # 4. Apply Selection (공통 메서드 사용)
                self._apply_popup_selection(popup)
                
                print("[DualFilterStrategy] HS Code applied via popup (Direct Input Mode).")

            except Exception as e:
                print(f"[DualFilterStrategy] Popup flow failed: {e}")
                raise e
        
        # C. Set Region to "All"
        print("[DualFilterStrategy] Setting Region to 'All'")
        
        # FIX: "Basic Type (2 items)" requires selecting the second item explicitly.
        # We must click "국내지역" to activate it.
        try:
            print("[DualFilterStrategy] Selecting second criteria: 국내지역")
            # Using ID #LOCATION_DIV as get_by_text("국내지역") is ambiguous due to help text on page
            page.click("#LOCATION_DIV")
            
            # 2. Select Location Type -> A (City)
            # <select id="LOCATION_TYPE" ...><option value="A">시 선택...
            print("[DualFilterStrategy] Selecting Location Type: 'City' (A)")
            page.wait_for_selector("#LOCATION_TYPE", state="visible")
            page.select_option("#LOCATION_TYPE", value="A")
            
            # 3. Next dropdown is 'All' by default (as per user), so skipping.
            page.wait_for_timeout(500)
            
        except Exception as e:
            print(f"[DualFilterStrategy] Failed to select '국내지역' options: {e}")
            raise e

        # D. Click Search
        print("[DualFilterStrategy] Clicking Search...")
        try:
            page.click("button[onclick*='goSearch']")
        except:
             page.get_by_text("조회").click()
        
        page.wait_for_timeout(3000) # Wait for grid results

        downloaded_files = []

        # 4. Iteration: Find Region in Results -> Download (리팩토링: 메서드 사용)
        for filter_value in filter_data_list:
            result = self._download_region_data(page, filter_value, save_path_dir, strategy_name)
            if result:
                downloaded_files.append(result)

        # 5. Merge Files and Create Unified Report using DataProcessor
        if not downloaded_files:
            print("[DualFilterStrategy] No files downloaded. Merge skipped.")
            return ""

        print(f"[DualFilterStrategy] Start merging {len(downloaded_files)} files...")
        all_data = []
        
        for file, filter_val in downloaded_files:
            try:
                # Read with MultiIndex headers (same as ExcelReaderAdapter)
                df = pd.read_excel(file, header=[2, 3])
                print(f"  - Loaded {os.path.basename(file)}: shape={df.shape}")
                all_data.append(df)
            except Exception as e:
                print(f"[DualFilterStrategy] Error reading {file}: {e}")

        if not all_data:
            print("[DualFilterStrategy] No valid DataFrames to merge.")
            return ""
        
        # Concatenate all region data
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"[DualFilterStrategy] Combined DataFrame shape: {combined_df.shape}")
        
        # Use DataProcessor to convert to report format
        from domain.services.data_processor import DataProcessor
        processor = DataProcessor()
        
        report_df = processor.process(combined_df)
        print(f"[DualFilterStrategy] Report DataFrame shape: {report_df.shape}")
        print(f"[DualFilterStrategy] Columns: {report_df.columns.tolist()}")
        
        # Save to reports directory
        reports_dir = os.path.join(save_path_dir, "..", "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        report_filename = f"report_{strategy_name}.xlsx"
        report_path = os.path.join(reports_dir, report_filename)
        
        report_df.to_excel(report_path, index=False)
        print(f"[DualFilterStrategy] Saved report: {report_path}")
        
        print(f"[DualFilterStrategy] Downloaded files preserved in {save_path_dir}:")
        for file, region in downloaded_files:
            print(f"  - {os.path.basename(file)} ({region})")
        
        return report_path
    
    # ========== 지역별 다운로드 메서드 ==========
    
    def _find_region_cell(self, page: Page, region_name: str):
        """
        특정 지역의 셀(Locator)을 찾기
        
        Args:
            page: Playwright Page 객체
            region_name: 지역 이름 (예: "부산", "경남")
            
        Returns:
            Locator 객체 (찾지 못하면 count()가 0)
        """
        # 1. Try finding by title attribute
        locator = page.locator(f"td[role='gridcell'][title='{region_name}'] font")
        
        # 2. Fallback: Try finding by text
        if locator.count() == 0:
            locator = page.locator(f"td[role='gridcell'] font:text-is('{region_name}')")
        
        return locator
    
    def _download_region_data(
        self,
        page: Page,
        region_name: str,
        save_dir: str,
        strategy_name: str
    ) -> tuple[str, str] | None:
        """
        특정 지역의 데이터를 다운로드
        
        Args:
            page: Playwright Page 객체
            region_name: 지역 이름
            save_dir: 저장 디렉토리
            strategy_name: Strategy 이름 (파일명에 사용)
            
        Returns:
            (파일 경로, 지역 이름) 튜플 또는 None (실패 시)
        """
        print(f"\n[DualFilterStrategy] Processing Region: {region_name}")
        
        try:
            # 1. 지역 셀 찾기
            target_region_locator = self._find_region_cell(page, region_name)
            
            if target_region_locator.count() == 0:
                print(f"[DualFilterStrategy] Region '{region_name}' not found in search results.")
                return None
            
            print(f"[DualFilterStrategy] Found target region: {region_name}")
            
            # 2. 상세 팝업 열기
            with page.expect_popup() as popup_info:
                target_region_locator.first.click()
            
            detail_popup = popup_info.value
            detail_popup.wait_for_load_state()
            print(f"[DualFilterStrategy] Detail popup opened for {region_name}")
            
            try:
                # 3. Dialog 자동 수락
                detail_popup.on("dialog", lambda dialog: dialog.accept())
                
                # 4. 데이터 로드 대기
                try:
                    detail_popup.wait_for_selector("td[role='gridcell']", timeout=15000)
                except:
                    detail_popup.wait_for_selector("td", timeout=15000)
                
                # 5. 다운로드 실행
                try:
                    with detail_popup.expect_download(timeout=60000) as download_info:
                        # 다운로드 버튼 찾기 및 클릭
                        grid_excel_btn = detail_popup.locator("a[href*='GridtoExcel']")
                        if grid_excel_btn.count() > 0:
                            grid_excel_btn.first.click(force=True)
                        elif detail_popup.get_by_text("다운로드").count() > 0:
                            detail_popup.get_by_text("다운로드").first.click(force=True)
                        else:
                            detail_popup.locator("button").filter(has_text="다운로드").first.click(force=True)
                    
                    download = download_info.value
                    print(f"[DualFilterStrategy] Download started: {download.suggested_filename}")
                    
                    # 6. 파일 저장
                    suggested_name = download.suggested_filename
                    file_ext = os.path.splitext(suggested_name)[1] or ".xls"
                    
                    timestamp = int(time.time())
                    filename = f"temp_{strategy_name}_{region_name}_{timestamp}{file_ext}"
                    save_path = os.path.join(save_dir, filename)
                    download.save_as(save_path)
                    
                    print(f"[DualFilterStrategy] Downloaded: {save_path}")
                    return (save_path, region_name)
                    
                except Exception as dl_error:
                    print(f"[DualFilterStrategy] Download failed: {dl_error}")
                    raise dl_error
            
            except Exception as popup_e:
                print(f"[DualFilterStrategy] Error inside popup for {region_name}: {popup_e}")
                return None
            
            finally:
                try:
                    detail_popup.close()
                    print(f"[DualFilterStrategy] Closed popup for {region_name}")
                except:
                    pass
        
        except Exception as e:
            print(f"[DualFilterStrategy] Error processing {region_name}: {e}")
            return None
