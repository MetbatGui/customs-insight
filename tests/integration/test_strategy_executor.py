"""
통합 테스트: StrategyExecutor

Strategy 객체 기반 스크래핑 실행 서비스의 동작을 검증합니다.
로그 출력을 캡처하여 올바른 워크플로우가 실행되는지 확인합니다.
"""

import unittest
import tomllib
import os
import io
import sys
from unittest.mock import Mock
from src.domain.models import Strategy
from src.infra.services.strategy_executor import StrategyExecutor


class TestStrategyExecutor(unittest.TestCase):
    """StrategyExecutor 통합 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        self.executor = StrategyExecutor()
        self.mock_page = Mock()
        
        # 프로젝트 루트 찾기
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
        self.strategies_dir = os.path.join(self.project_root, "strategies")
    
    def _load_strategy(self, filename: str) -> Strategy:
        """TOML 파일에서 Strategy 로드"""
        toml_path = os.path.join(self.strategies_dir, filename)
        
        with open(toml_path, "rb") as f:
            toml_dict = tomllib.load(f)
        
        return Strategy.from_toml_dict(toml_dict)
    
    def _capture_output(self, func, *args, **kwargs):
        """함수 실행 중 출력 캡처"""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            result = func(*args, **kwargs)
        finally:
            sys.stdout = sys.__stdout__
        
        return result, captured_output.getvalue()
    
    def test_execute_apr_strategy(self):
        """에이피알 전략 실행 테스트 (2개 품목, 국내지역 필터)"""
        strategy = self._load_strategy("에이피알.toml")
        
        results, output = self._capture_output(
            self.executor.execute,
            self.mock_page,
            "data",
            strategy
        )
        
        # 결과 검증
        self.assertEqual(len(results), 2, "Should download 2 files (2 items)")
        self.assertIn("화장품", results[0])
        self.assertIn("미용기기", results[1])
        
        # 로그 검증
        self.assertIn("에이피알", output)
        
        # 품목 1: 화장품
        self.assertIn("화장품", output)
        self.assertIn("3304991000", output)
        self.assertIn("국내지역", output)
        self.assertIn("시군구", output)
        self.assertIn("서울 송파구", output)
        
        # 품목 2: 미용기기
        self.assertIn("미용기기", output)
        self.assertIn("8543702010", output)
        
        # 14단계 워크플로우 검증
        self.assertIn("[1]", output)  # 품목/성질별
        self.assertIn("[2]", output)  # 드롭다운
        self.assertIn("[3]", output)  # 검색하기
        self.assertIn("[4]", output)  # HS Code
        self.assertIn("[5]", output)  # 직접입력추가
        self.assertIn("[6]", output)  # 선택적용
        self.assertIn("[7]", output)  # 필터 선택
        self.assertIn("[8]", output)  # scope/세관
        self.assertIn("[9]", output)  # 지역
        self.assertIn("[10]", output)  # 조회하기
        self.assertIn("[11]", output)  # 금액 클릭
        self.assertIn("[12]", output)  # 다운로드
        self.assertIn("[13]", output)  # 얼럿
        
        # print("\n" + output)  # Windows console handle error 방지
    
    def test_execute_nongshim_strategy(self):
        """농심 전략 실행 테스트 (1개 품목, 국내지역 필터)"""
        strategy = self._load_strategy("농심.toml")
        
        results, output = self._capture_output(
            self.executor.execute,
            self.mock_page,
            "data",
            strategy
        )
        
        # 결과 검증
        self.assertEqual(len(results), 1, "Should download 1 file (1 item)")
        self.assertIn("라면", results[0])
        
        # 로그 검증
        self.assertIn("농심", output)
        self.assertIn("라면", output)
        self.assertIn("1902301010", output)
        self.assertIn("국내지역", output)
        self.assertIn("시", output)
        self.assertIn("부산", output)
    
    def test_execute_hyosung_strategy(self):
        """효성중공업 전략 실행 테스트 (1개 품목, 세관 필터)"""
        strategy = self._load_strategy("효성중공업.toml")
        
        results, output = self._capture_output(
            self.executor.execute,
            self.mock_page,
            "data",
            strategy
        )
        
        # 결과 검증
        self.assertEqual(len(results), 1, "Should download 1 file (1 item)")
        
        # 로그 검증
        self.assertIn("효성중공업", output)
        self.assertIn("8504230000", output)
        self.assertIn("세관", output)
        self.assertIn("창원세관", output)
    
    def test_execute_pharma_research_strategy(self):
        """파마리서치 전략 실행 테스트 (1개 품목, 필터 없음)"""
        strategy = self._load_strategy("파마리서치.toml")
        
        results, output = self._capture_output(
            self.executor.execute,
            self.mock_page,
            "data",
            strategy
        )
        
        # 결과 검증
        self.assertEqual(len(results), 1, "Should download 1 file (1 item)")
        
        # 로그 검증
        self.assertIn("파마리서치", output)
        self.assertIn("3304999000", output)
        self.assertIn("No filters to apply", output)
    
    def test_strategy_items_count(self):
        """각 전략의 품목 수 검증"""
        apr = self._load_strategy("에이피알.toml")
        nongshim = self._load_strategy("농심.toml")
        
        self.assertEqual(len(apr.items), 2, "APR should have 2 items")
        self.assertEqual(len(nongshim.items), 1, "Nongshim should have 1 item")
    
    def test_filter_type_detection(self):
        """필터 타입별 분기 테스트"""
        # 국내지역 필터
        domestic_strategy = self._load_strategy("농심.toml")
        _, domestic_output = self._capture_output(
            self.executor.execute,
            self.mock_page,
            "data",
            domestic_strategy
        )
        self.assertIn("국내지역", domestic_output)
        self.assertIn("scope", domestic_output.lower())
        
        # 세관 필터
        customs_strategy = self._load_strategy("효성중공업.toml")
        _, customs_output = self._capture_output(
            self.executor.execute,
            self.mock_page,
            "data",
            customs_strategy
        )
        self.assertIn("세관", customs_output)
        self.assertIn("customs office", customs_output.lower())


if __name__ == '__main__':
    unittest.main()
