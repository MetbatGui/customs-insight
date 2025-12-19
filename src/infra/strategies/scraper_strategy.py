from abc import ABC, abstractmethod
from playwright.sync_api import Page, Download
import time
import os
import pandas as pd
from typing import Dict, Any, Optional
from pathlib import Path
from returns.result import Result, Success, Failure, safe


class ScraperStrategy(ABC):
    """
    Base Strategy 클래스
    
    공통 로직을 제공하며, 각 Strategy는 execute()만 구현하면 됨
    """
    
    @abstractmethod
    def execute(self, page: Page, save_path_dir: str, strategy_config: dict = None) -> str:
        """
        Executes the scraping strategy.
        
        Args:
            page: The Playwright Page object (already logged in).
            save_path_dir: Directory to save the downloaded file.
            strategy_config: Dictionary containing strategy configuration (e.g., HS Code).
            
        Returns:
            The full path to the downloaded/processed file.
        """
        pass
    
    # ========== 공통 메서드 ==========
    
    def _parse_config(self, strategy_config: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """
        Config에서 공통 값 추출
        
        Args:
            strategy_config: Strategy 설정 딕셔너리
            
        Returns:
            파싱된 설정값 {'hs_code', 'target_text', 'strategy_name'}
        """
        hs_code = "8504230000"
        target_text = ""
        strategy_name = ""
        
        if strategy_config:
            if 'search' in strategy_config:
                hs_code = strategy_config['search'].get('hs_code', hs_code)
                target_text = strategy_config['search'].get('target_text', target_text)
            
            if 'name' in strategy_config:
                strategy_name = f"_{strategy_config['name']}"
        
        return {
            'hs_code': hs_code,
            'target_text': target_text,
            'strategy_name': strategy_name
        }
    
    def _navigate_to_url(self, page: Page, url: str) -> None:
        """
        URL 이동 및 로드 대기
        
        Args:
            page: Playwright Page 객체
            url: 이동할 URL
        """
        page.goto(url)
        page.wait_for_load_state('networkidle')
    
    def _save_download(
        self,
        download: Download,
        save_path_dir: str,
        strategy_name: str = ""
    ) -> str:
        """
        다운로드 파일 저장 및 XLS → XLSX 변환 (기존 인터페이스)
        
        하위 호환성을 위해 유지. 내부적으로 _save_download_safe 사용
        
        Args:
            download: Playwright Download 객체
            save_path_dir: 저장 디렉토리
            strategy_name: Strategy 이름 (파일명에 사용)
            
        Returns:
            저장된 XLSX 파일 경로 (변환 실패 시 XLS 경로)
        """
        result = self._save_download_safe(download, save_path_dir, strategy_name)
        return result.value_or("")
    
    def _save_download_safe(
        self,
        download: Download,
        save_path_dir: str,
        strategy_name: str = ""
    ) -> Result[str, str]:
        """
        다운로드 파일 저장 및 XLS → XLSX 변환 (Result 타입)
        
        Args:
            download: Playwright Download 객체
            save_path_dir: 저장 디렉토리
            strategy_name: Strategy 이름 (파일명에 사용)
            
        Returns:
            Result[str, str]
            - Success: 저장된 XLSX 파일 경로
            - Failure: 에러 메시지
        """
        try:
            timestamp = int(time.time())
            filename_xls = f"bandtrass_{timestamp}{strategy_name}.xls"
            full_path_xls = os.path.join(save_path_dir, filename_xls)
            
            # XLS 파일 저장
            download.save_as(full_path_xls)
            print(f"[ScraperStrategy] Download saved: {full_path_xls}")
            
            # XLS → XLSX 변환
            return self._convert_xls_to_xlsx_safe(full_path_xls, save_path_dir, timestamp)
            
        except Exception as e:
            return Failure(f"Download save failed: {str(e)}")
    
    def _convert_xls_to_xlsx(
        self,
        xls_path: str,
        save_dir: str,
        timestamp: int
    ) -> str:
        """
        XLS 파일을 XLSX로 변환 (기존 인터페이스)
        
        하위 호환성을 위해 유지. 내부적으로 _convert_xls_to_xlsx_safe 사용
        
        Args:
            xls_path: XLS 파일 경로
            save_dir: 저장 디렉토리
            timestamp: 타임스탬프
            
        Returns:
            XLSX 파일 경로 (실패 시 원본 XLS 경로)
        """
        result = self._convert_xls_to_xlsx_safe(xls_path, save_dir, timestamp)
        return result.value_or(xls_path)
    
    def _convert_xls_to_xlsx_safe(
        self,
        xls_path: str,
        save_dir: str,
        timestamp: int
    ) -> Result[str, str]:
        """
        XLS 파일을 XLSX로 변환 (Result 타입)
        
        Args:
            xls_path: XLS 파일 경로
            save_dir: 저장 디렉토리
            timestamp: 타임스탬프
            
        Returns:
            Result[str, str]
            - Success: XLSX 파일 경로
            - Failure: 에러 메시지
        """
        try:
            print("[ScraperStrategy] Converting XLS to XLSX...")
            df = pd.read_excel(xls_path)
            
            filename_xlsx = f"bandtrass_{timestamp}.xlsx"
            full_path_xlsx = os.path.join(save_dir, filename_xlsx)
            
            df.to_excel(full_path_xlsx, index=False)
            print(f"[ScraperStrategy] Saved as: {full_path_xlsx}")
            
            # 원본 XLS 삭제
            os.remove(xls_path)
            
            return Success(full_path_xlsx)
            
        except Exception as e:
            error_msg = f"Conversion failed: {str(e)}"
            print(f"[ScraperStrategy] {error_msg}")
            return Failure(error_msg)
    
    def _open_item_search_popup(self, page: Page) -> Page:
        """
        품목 검색 팝업 열기
        
        Args:
            page: Playwright Page 객체
            
        Returns:
            팝업 Page 객체
        """
        page.wait_for_selector("#POPUP1", state="visible")
        
        with page.expect_popup() as popup_info:
            page.click("#POPUP1")
        
        popup = popup_info.value
        popup.wait_for_load_state()
        
        return popup
    
    def _search_hs_code_in_popup(self, popup: Page, hs_code: str) -> None:
        """
        팝업에서 HS Code 검색
        
        Args:
            popup: 팝업 Page 객체
            hs_code: 검색할 HS Code
        """
        popup.wait_for_selector("#CustomText")
        popup.fill("#CustomText", hs_code)
        popup.click("#CustomCheck")
        time.sleep(0.5)
    
    def _apply_popup_selection(self, popup: Page) -> None:
        """
        팝업 선택 적용 및 닫기
        
        Args:
            popup: 팝업 Page 객체
        """
        try:
            with popup.expect_event("close"):
                popup.get_by_text("선택적용", exact=True).click()
        except:
            if not popup.is_closed():
                popup.get_by_text("선택적용", exact=True).click()
