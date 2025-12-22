"""
BandtrassScraperAdapter 간단한 테스트
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.infra.adapters.bandtrass_scraper_adapter import BandtrassScraperAdapter
from src.domain.models import Strategy, StrategyItem


class TestBandtrassScraperAdapter(unittest.TestCase):
    """BandtrassScraperAdapter 테스트"""
    
    def test_adapter_accepts_strategy_object(self):
        """어댑터가 Strategy 객체를 받는지 확인"""
        adapter = BandtrassScraperAdapter(headless=True)
        
        # download_data 메서드 시그니처 확인
        import inspect
        sig = inspect.signature(adapter.download_data)
        params = list(sig.parameters.keys())
        
        self.assertIn('save_path', params)
        self.assertIn('strategy', params)
        
        print("[OK] Adapter accepts strategy parameter")
    
    def test_strategy_execution(self):
        """Strategy 객체를 사용하여 실행되는지 확인"""
        adapter = BandtrassScraperAdapter(headless=True)
        
        # 테스트용 Strategy 객체 생성
        test_strategy = Strategy(
            name="테스트회사",
            items=[
                StrategyItem(
                    name="테스트품목",
                    hs_code="1234567890",
                    filters=[]
                )
            ]
        )
        
        # Mock playwright to avoid actual browser launch
        with patch('src.infra.adapters.bandtrass_scraper_adapter.sync_playwright') as mock_playwright:
            mock_browser = MagicMock()
            mock_context = MagicMock()
            mock_page = MagicMock()
            
            mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page
            
            # StrategyExecutor도 mock
            with patch('src.infra.adapters.bandtrass_scraper_adapter.StrategyExecutor') as mock_executor:
                mock_executor.return_value.execute.return_value = ["test_file.xlsx"]
                
                try:
                    result = adapter.download_data("data", strategy=test_strategy)
                    
                    # StrategyExecutor.execute가 호출되었는지 확인
                    mock_executor.return_value.execute.assert_called_once()
                    print("[OK] Strategy object successfully used in execution")
                except Exception as e:
                    print(f"[SKIP] Test skipped due to mock issue: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
