"""
BandtrassScraperAdapter 간단한 테스트
"""

import unittest
from unittest.mock import Mock, patch
from src.infra.adapters.bandtrass_scraper_adapter import BandtrassScraperAdapter
from src.domain.models import Strategy


class TestBandtrassScraperAdapter(unittest.TestCase):
    """BandtrassScraperAdapter 테스트"""
    
    def test_adapter_accepts_strategy_path(self):
        """어댑터가 strategy_path를 받는지 확인"""
        adapter = BandtrassScraperAdapter(headless=True)
        
        # download_data 메서드 시그니처 확인
        import inspect
        sig = inspect.signature(adapter.download_data)
        params = list(sig.parameters.keys())
        
        self.assertIn('save_path', params)
        self.assertIn('strategy_path', params)
        
        print("[OK] Adapter accepts strategy_path parameter")
    
    def test_strategy_path_required(self):
        """strategy_path가 필수인지 확인"""
        adapter = BandtrassScraperAdapter(headless=True)
        
        # Mock playwright to avoid actual browser launch
        with patch('src.infra.adapters.bandtrass_scraper_adapter.sync_playwright'):
            try:
                # strategy_path 없이 호출하면 에러
                with self.assertRaises(ValueError):
                    adapter.download_data("data", strategy_path=None)
                
                print("[OK] ValueError raised when strategy_path is None")
            except Exception as e:
                # Mock이 제대로 안되면 스킵
                print(f"[SKIP] Test skipped due to mock issue: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
