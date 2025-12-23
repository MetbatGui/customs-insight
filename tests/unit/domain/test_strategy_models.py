"""
Tests for Strategy models

테스트 목적:
1. 필터 클래스 검증
2. Strategy 클래스 검증
3. TOML 파일 파싱 테스트
"""

import unittest
import os
from pydantic import ValidationError
from src.domain.models import (
    Filter,
    DomesticRegionFilter,
    CustomsOfficeFilter,
    StrategyItem,
    Strategy
)


class TestDomesticRegionFilter(unittest.TestCase):
    """DomesticRegionFilter 테스트"""
    
    def test_create_valid_filter(self):
        """유효한 국내지역 필터 생성"""
        filter = DomesticRegionFilter(
            scope="시",
            regions=["부산"]
        )
        
        self.assertEqual(filter.category, "국내지역")
        self.assertEqual(filter.scope, "시")
        self.assertEqual(filter.regions, ["부산"])
    
    def test_scope_validation(self):
        """scope는 '시' 또는 '시군구'만 허용"""
        # 유효한 값
        filter1 = DomesticRegionFilter(scope="시", regions=["서울"])
        filter2 = DomesticRegionFilter(scope="시군구", regions=["경남 창원시"])
        
        self.assertEqual(filter1.scope, "시")
        self.assertEqual(filter2.scope, "시군구")
        
        # 잘못된 값
        with self.assertRaises(ValidationError):
            DomesticRegionFilter(scope="도", regions=["경남"])
    
    def test_empty_regions_rejected(self):
        """빈 지역 리스트 거부"""
        with self.assertRaises(ValidationError):
            DomesticRegionFilter(scope="시", regions=[])
    
    def test_immutability(self):
        """불변성 테스트"""
        filter = DomesticRegionFilter(scope="시", regions=["부산"])
        
        with self.assertRaises(ValidationError):
            filter.regions = ["서울"]


class TestCustomsOfficeFilter(unittest.TestCase):
    """CustomsOfficeFilter 테스트"""
    
    def test_create_valid_filter(self):
        """유효한 세관 필터 생성"""
        filter = CustomsOfficeFilter(customs_offices=["창원세관"])
        
        self.assertEqual(filter.category, "세관")
        self.assertEqual(filter.customs_offices, ["창원세관"])
    
    def test_multiple_customs_offices(self):
        """여러 세관 리스트"""
        filter = CustomsOfficeFilter(customs_offices=["창원세관", "울산세관"])
        
        self.assertEqual(len(filter.customs_offices), 2)
    
    def test_empty_customs_offices_rejected(self):
        """빈 세관 리스트 거부"""
        with self.assertRaises(ValidationError):
            CustomsOfficeFilter(customs_offices=[])


class TestStrategyItem(unittest.TestCase):
    """StrategyItem 테스트"""
    
    def test_create_item_with_filter(self):
        """필터 포함 품목 생성"""
        item = StrategyItem(
            name="라면",
            hs_code="1902301010",
            filters=[
                DomesticRegionFilter(scope="시", regions=["부산"])
            ]
        )
        
        self.assertEqual(item.name, "라면")
        self.assertEqual(item.hs_code, "1902301010")
        self.assertEqual(len(item.filters), 1)
    
    def test_create_item_without_filter(self):
        """필터 없는 품목 생성"""
        item = StrategyItem(
            name="화장품",
            hs_code="3304999000",
            filters=[]
        )
        
        self.assertEqual(len(item.filters), 0)
    
    def test_hs_code_validation(self):
        """HS Code는 10자리 숫자만 허용"""
        # 유효한 값
        item = StrategyItem(name="라면", hs_code="1902301010")
        self.assertEqual(item.hs_code, "1902301010")
        
        # 잘못된 값: 9자리
        with self.assertRaises(ValidationError):
            StrategyItem(name="라면", hs_code="190230101")
        
        # 잘못된 값: 11자리
        with self.assertRaises(ValidationError):
            StrategyItem(name="라면", hs_code="19023010100")
        
        # 잘못된 값: 문자 포함
        with self.assertRaises(ValidationError):
            StrategyItem(name="라면", hs_code="190230101a")
    
    def test_multiple_filters(self):
        """여러 필터 조합"""
        item = StrategyItem(
            name="변압기",
            hs_code="8504230000",
            filters=[
                DomesticRegionFilter(scope="시군구", regions=["경남 창원시"]),
                CustomsOfficeFilter(customs_offices=["창원세관"])
            ]
        )
        
        self.assertEqual(len(item.filters), 2)
        self.assertIsInstance(item.filters[0], DomesticRegionFilter)
        self.assertIsInstance(item.filters[1], CustomsOfficeFilter)


class TestStrategy(unittest.TestCase):
    """Strategy 테스트"""
    
    def test_create_strategy(self):
        """전략 생성"""
        strategy = Strategy(
            name="농심",
            items=[
                StrategyItem(
                    name="라면",
                    hs_code="1902301010",
                    filters=[DomesticRegionFilter(scope="시", regions=["부산"])]
                )
            ]
        )
        
        self.assertEqual(strategy.name, "농심")
        self.assertEqual(len(strategy.items), 1)
    
    def test_empty_items_rejected(self):
        """빈 품목 리스트 거부"""
        with self.assertRaises(ValidationError):
            Strategy(name="테스트", items=[])
    
    def test_immutability(self):
        """전략 불변성"""
        strategy = Strategy(
            name="농심",
            items=[StrategyItem(name="라면", hs_code="1902301010")]
        )
        
        with self.assertRaises(ValidationError):
            strategy.name = "수정"


class TestStrategyFromToml(unittest.TestCase):
    """TOML 파일 파싱 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        import tomllib
        self.tomllib = tomllib
        
        # 프로젝트 루트 찾기
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
        self.strategies_dir = os.path.join(self.project_root, "strategies")
    
    def test_parse_nongshim_toml(self):
        """농심.toml 파싱"""
        toml_path = os.path.join(self.strategies_dir, "농심.toml")
        
        with open(toml_path, "rb") as f:
            toml_dict = self.tomllib.load(f)
        
        strategy = Strategy.from_toml_dict(toml_dict)
        
        self.assertEqual(strategy.name, "농심")
        self.assertEqual(len(strategy.items), 1)
        self.assertEqual(strategy.items[0].name, "라면")
        self.assertEqual(strategy.items[0].hs_code, "1902301010")
        self.assertEqual(len(strategy.items[0].filters), 1)
        self.assertIsInstance(strategy.items[0].filters[0], DomesticRegionFilter)
        self.assertEqual(strategy.items[0].filters[0].scope, "시")
        self.assertEqual(strategy.items[0].filters[0].regions, ["부산"])
    
    def test_parse_hyosung_toml(self):
        """효성중공업.toml 파싱 (세관 필터)"""
        toml_path = os.path.join(self.strategies_dir, "효성중공업.toml")
        
        with open(toml_path, "rb") as f:
            toml_dict = self.tomllib.load(f)
        
        strategy = Strategy.from_toml_dict(toml_dict)
        
        self.assertEqual(strategy.name, "효성중공업")
        self.assertEqual(len(strategy.items[0].filters), 1)
        self.assertIsInstance(strategy.items[0].filters[0], CustomsOfficeFilter)
        self.assertEqual(strategy.items[0].filters[0].customs_offices, ["창원세관"])
    
    def test_parse_hyundai_rotem_toml(self):
        """현대로템.toml 파싱 (시군구 scope)"""
        toml_path = os.path.join(self.strategies_dir, "현대로템.toml")
        
        with open(toml_path, "rb") as f:
            toml_dict = self.tomllib.load(f)
        
        strategy = Strategy.from_toml_dict(toml_dict)
        
        self.assertEqual(strategy.name, "현대로템")
        self.assertEqual(strategy.items[0].filters[0].scope, "시군구")
        self.assertEqual(strategy.items[0].filters[0].regions, ["경남 창원시"])
    
    def test_parse_apr_toml(self):
        """에이피알.toml 파싱 (다중 품목)"""
        toml_path = os.path.join(self.strategies_dir, "에이피알.toml")
        
        with open(toml_path, "rb") as f:
            toml_dict = self.tomllib.load(f)
        
        strategy = Strategy.from_toml_dict(toml_dict)
        
        self.assertEqual(strategy.name, "에이피알")
        self.assertEqual(len(strategy.items), 2)
        self.assertEqual(strategy.items[0].name, "화장품")
        self.assertEqual(strategy.items[1].name, "미용기기")
    
    def test_parse_pharma_research_toml(self):
        """파마리서치.toml 파싱 (국내지역 필터)"""
        toml_path = os.path.join(self.strategies_dir, "파마리서치.toml")
        
        with open(toml_path, "rb") as f:
            toml_dict = self.tomllib.load(f)
        
        strategy = Strategy.from_toml_dict(toml_dict)
        
        self.assertEqual(strategy.name, "파마리서치")
        # 파마리서치는 이제 국내지역 필터가 있음
        self.assertEqual(len(strategy.items[0].filters), 1)
        self.assertIsInstance(strategy.items[0].filters[0], DomesticRegionFilter)
    
    def test_parse_samyang_toml(self):
        """삼양.toml 파싱 (다중 지역)"""
        toml_path = os.path.join(self.strategies_dir, "삼양.toml")
        
        with open(toml_path, "rb") as f:
            toml_dict = self.tomllib.load(f)
        
        strategy = Strategy.from_toml_dict(toml_dict)
        
        self.assertEqual(strategy.name, "삼양")
        self.assertEqual(strategy.items[0].filters[0].regions, ["경남", "강원"])
    
    def test_parse_hd_hyundai_electric_toml(self):
        """HD현대일렉트릭.toml 파싱 (세관 필터)"""
        toml_path = os.path.join(self.strategies_dir, "HD현대일렉트릭.toml")
        
        with open(toml_path, "rb") as f:
            toml_dict = self.tomllib.load(f)
        
        strategy = Strategy.from_toml_dict(toml_dict)
        
        self.assertEqual(strategy.name, "HD현대일렉트릭")
        self.assertEqual(len(strategy.items[0].filters), 1)
        self.assertIsInstance(strategy.items[0].filters[0], CustomsOfficeFilter)
        self.assertEqual(strategy.items[0].filters[0].customs_offices, ["울산세관"])
    
    def test_parse_hanwha_aerospace_toml(self):
        """한화에어로스페이스.toml 파싱 (국내지역 필터)"""
        toml_path = os.path.join(self.strategies_dir, "한화에어로스페이스.toml")
        
        with open(toml_path, "rb") as f:
            toml_dict = self.tomllib.load(f)
        
        strategy = Strategy.from_toml_dict(toml_dict)
        
        self.assertEqual(strategy.name, "한화에어로스페이스")
        self.assertEqual(len(strategy.items[0].filters), 1)
        self.assertIsInstance(strategy.items[0].filters[0], DomesticRegionFilter)
        self.assertEqual(strategy.items[0].filters[0].scope, "시군구")
        self.assertEqual(strategy.items[0].filters[0].regions, ["경남 창원시"])


if __name__ == '__main__':
    unittest.main()
