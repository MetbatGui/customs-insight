from abc import ABC, abstractmethod
from playwright.sync_api import Page, Download
import time
import os
import pandas as pd
from typing import Dict, Any, Optional
from pathlib import Path
from returns.result import Result, Success, Failure, safe


class ScraperStrategy(ABC):
    """웹 스크래핑 전략의 기본 클래스입니다.
    
    이 추상 클래스는 Bandtrass 웹사이트에서 데이터를 스크래핑하기 위한
    공통 메서드와 인터페이스를 정의합니다.
    
    각 구체적인 전략(SingleFilterStrategy, DualFilterStrategy 등)은
    이 클래스를 상속받아 execute() 메서드를 구현해야 합니다.
    
    주요 기능:
        - Config 파싱
        - URL 네비게이션
        - 파일 다운로드 및 변환 (XLS → XLSX)
        - 팝업 처리
    
    Attributes:
        없음 (상태를 가지지 않음)
    
    Examples:
        >>> class CustomStrategy(ScraperStrategy):
        ...     def execute(self, page, save_dir, config):
        ...         return self._download_and_process(page, save_dir)
    """
    
    @abstractmethod
    def execute(self, page: Page, save_path_dir: str, strategy_config: dict = None) -> str:
        """스크래핑 전략을 실행합니다.
        
        Args:
            page: 이미 로그인된 Playwright Page 객체.
            save_path_dir: 다운로드한 파일을 저장할 디렉토리.
            strategy_config: 전략 설정 딕셔너리 (HS Code 등 포함).
        
        Returns:
            다운로드/처리된 파일의 전체 경로.
        
        Raises:
            NotImplementedError: 하위 클래스에서 구현하지 않은 경우.
        """
        pass
    
    def _parse_config(self, strategy_config: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Strategy 설정에서 공통 값을 추출합니다.
        
        Args:
            strategy_config: Strategy 설정 딕셔너리.
                'search' 키에 'hs_code', 'target_text'를 포함할 수 있음.
                'name' 키에 strategy 이름을 포함할 수 있음.
        
        Returns:
            파싱된 설정값을 포함하는 딕셔너리:
                - hs_code (str): HS Code
                - target_text (str): 검색 대상 텍스트
                - strategy_name (str): Strategy 이름 (파일명에 사용, "_"로 시작)
        
        Examples:
            >>> config = self._parse_config({'search': {'hs_code': '1234567890'}})
            >>> print(config['hs_code'])
            1234567890
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
        """지정된 URL로 이동하고 로드를 기다립니다.
        
        Args:
            page: Playwright Page 객체.
            url: 이동할 URL.
        
        Note:
            networkidle 상태까지 대기하여 안정적인 페이지 로드를 보장합니다.
        """
        page.goto(url)
        page.wait_for_load_state('networkidle')
    
    def _save_download(
        self,
        download: Download,
        save_path_dir: str,
        strategy_name: str = ""
    ) -> str:
        """다운로드 파일을 저장하고 XLS를 XLSX로 변환합니다.
        
        내부적으로 _save_download_safe를 호출하여 Result 타입으로 처리하고,
        실패 시 빈 문자열을 반환합니다.
        
        Args:
            download: Playwright Download 객체.
            save_path_dir: 저장 디렉토리.
            strategy_name: Strategy 이름 (파일명에 추가).
        
        Returns:
            저장된 XLSX 파일 경로. 실패 시 빈 문자열.
        
        Note:
            하위 호환성을 위해 유지하는 메서드입니다.
        """
        result = self._save_download_safe(download, save_path_dir, strategy_name)
        return result.value_or("")
    
    def _save_download_safe(
        self,
        download: Download,
        save_path_dir: str,
        strategy_name: str = ""
    ) -> Result[str, str]:
        """다운로드 파일을 저장하고 XLS를 XLSX로 변환합니다 (Result 타입).
        
        Args:
            download: Playwright Download 객체.
            save_path_dir: 저장 디렉토리.
            strategy_name: Strategy 이름 (파일명에 추가).
        
        Returns:
            Result[str, str]:
                - Success: 저장된 XLSX 파일 경로
                - Failure: 에러 메시지
        
        Examples:
            >>> result = self._save_download_safe(download, "data", "_삼양")
            >>> if isinstance(result, Success):
            ...     print(f"Saved: {result.unwrap()}")
        """
        try:
            timestamp = int(time.time())
            filename_xls = f"bandtrass_{timestamp}{strategy_name}.xls"
            full_path_xls = os.path.join(save_path_dir, filename_xls)
            
            download.save_as(full_path_xls)
            print(f"[ScraperStrategy] Download saved: {full_path_xls}")
            
            return self._convert_xls_to_xlsx_safe(full_path_xls, save_path_dir, timestamp)
            
        except Exception as e:
            return Failure(f"Download save failed: {str(e)}")
    
    def _convert_xls_to_xlsx(
        self,
        xls_path: str,
        save_dir: str,
        timestamp: int
    ) -> str:
        """XLS 파일을 XLSX로 변환합니다.
        
        내부적으로 _convert_xls_to_xlsx_safe를 호출하여 Result 타입으로 처리하고,
        실패 시 원본 XLS 경로를 반환합니다.
        
        Args:
            xls_path: XLS 파일 경로.
            save_dir: 저장 디렉토리.
            timestamp: 타임스탬프 (파일명에 사용).
        
        Returns:
            XLSX 파일 경로. 실패 시 원본 XLS 경로.
        
        Note:
            하위 호환성을 위해 유지하는 메서드입니다.
        """
        result = self._convert_xls_to_xlsx_safe(xls_path, save_dir, timestamp)
        return result.value_or(xls_path)
    
    def _convert_xls_to_xlsx_safe(
        self,
        xls_path: str,
        save_dir: str,
        timestamp: int
    ) -> Result[str, str]:
        """XLS 파일을 XLSX로 변환합니다 (Result 타입).
        
        pandas를 사용하여 XLS 파일을 읽고 XLSX 형식으로 저장합니다.
        변환 성공 시 원본 XLS 파일을 삭제합니다.
        
        Args:
            xls_path: XLS 파일 경로.
            save_dir: 저장 디렉토리.
            timestamp: 타임스탬프 (파일명에 사용).
        
        Returns:
            Result[str, str]:
                - Success: XLSX 파일 경로
                - Failure: 에러 메시지
        
        Note:
            변환 실패 시 원본 XLS 파일은 그대로 유지됩니다.
        """
        try:
            print("[ScraperStrategy] Converting XLS to XLSX...")
            df = pd.read_excel(xls_path)
            
            filename_xlsx = f"bandtrass_{timestamp}.xlsx"
            full_path_xlsx = os.path.join(save_dir, filename_xlsx)
            
            df.to_excel(full_path_xlsx, index=False)
            print(f"[ScraperStrategy] Saved as: {full_path_xlsx}")
            
            os.remove(xls_path)
            
            return Success(full_path_xlsx)
            
        except Exception as e:
            error_msg = f"Conversion failed: {str(e)}"
            print(f"[ScraperStrategy] {error_msg}")
            return Failure(error_msg)
    
    def _open_item_search_popup(self, page: Page) -> Page:
        """품목 검색 팝업을 엽니다.
        
        Args:
            page: Playwright Page 객체.
        
        Returns:
            열린 팝업의 Page 객체.
        
        Raises:
            TimeoutError: 팝업 버튼을 찾지 못한 경우.
        """
        page.wait_for_selector("#POPUP1", state="visible")
        
        with page.expect_popup() as popup_info:
            page.click("#POPUP1")
        
        popup = popup_info.value
        popup.wait_for_load_state()
        
        return popup
    
    def _search_hs_code_in_popup(self, popup: Page, hs_code: str) -> None:
        """팝업에서 HS Code를 검색합니다.
        
        Args:
            popup: 팝업 Page 객체.
            hs_code: 검색할 HS Code.
        
        Note:
            입력 후 0.5초 대기하여 안정성을 보장합니다.
        """
        popup.wait_for_selector("#CustomText")
        popup.fill("#CustomText", hs_code)
        popup.click("#CustomCheck")
        time.sleep(0.5)
    
    def _apply_popup_selection(self, popup: Page) -> None:
        """팝업 선택을 적용하고 닫습니다.
        
        Args:
            popup: 팝업 Page 객체.
        
        Note:
            팝업이 이미 닫혀있는 경우를 처리합니다.
        """
        try:
            with popup.expect_event("close"):
                popup.get_by_text("선택적용", exact=True).click()
        except:
            if not popup.is_closed():
                popup.get_by_text("선택적용", exact=True).click()
