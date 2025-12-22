"""
StrategyExecutor - Strategy 객체 기반 스크래핑 실행 서비스

Strategy 객체를 받아 각 품목을 순회하며 필터를 적용하고 데이터를 다운로드합니다.
현재는 로그 기반으로 동작하며, 추후 실제 Playwright 로직으로 대체할 수 있습니다.
"""

from typing import List
from playwright.sync_api import Page
from src.domain.models import Strategy, StrategyItem, DomesticRegionFilter, CustomsOfficeFilter


class StrategyExecutor:
    """
    Strategy 객체 기반 스크래핑 실행 서비스
    
    Strategy 객체를 받아 각 품목을 순회하며
    필터를 적용하고 데이터를 다운로드합니다.
    
    Example:
        >>> executor = StrategyExecutor()
        >>> results = executor.execute(page, "data", strategy)
        >>> print(results)
        ['data/에이피알_화장품.xlsx', 'data/에이피알_미용기기.xlsx']
    """
    
    def execute(self, page: Page, save_dir: str, strategy: Strategy) -> List[str]:
        """
        Strategy 실행
        
        Args:
            page: Playwright Page 객체 (현재는 Mock 가능)
            save_dir: 저장 디렉토리
            strategy: Strategy 객체
            
        Returns:
            다운로드된 파일 경로 리스트
        """
        print(f"\n{'='*60}")
        print(f"[StrategyExecutor] Executing Strategy: {strategy.name}")
        print(f"{'='*60}")
        
        results = []
        
        for idx, item in enumerate(strategy.items, 1):
            print(f"\n--- Item {idx}/{len(strategy.items)}: {item.name} ---")
            
            # 1-6: 품목 검색
            self._search_item(page, item)
            
            # 7-10: 필터 적용
            if item.filters:
                self._apply_filters(page, item.filters)
            else:
                print("  [Note] No filters to apply, proceeding to search")
            
            # 11-13: 데이터 다운로드
            file_path = self._download_data(page, save_dir, strategy.name, item.name)
            results.append(file_path)
        
        print(f"\n{'='*60}")
        print(f"[StrategyExecutor] Completed: {len(results)} files downloaded")
        print(f"{'='*60}\n")
        
        return results
    
    def _search_item(self, page: Page, item: StrategyItem):
        """
        품목 검색 (1-6단계)
        
        Args:
            page: Playwright Page 객체
            item: StrategyItem 객체
        """
        print(f"  [1] Clicking '품목/성질별/신성질별'")
        print(f"  [2] Selecting '품목' from dropdown")
        print(f"  [3] Clicking '품목 검색하기'")
        print(f"  [4] Entering HS Code in popup: {item.hs_code}")
        print(f"  [5] Clicking '직접입력추가'")
        print(f"  [6] Clicking '선택적용'")
    
    def _apply_filters(self, page: Page, filters):
        """
        필터 적용 (7-10단계)
        
        Args:
            page: Playwright Page 객체
            filters: 필터 리스트
        """
        for filter in filters:
            if isinstance(filter, DomesticRegionFilter):
                self._apply_domestic_region_filter(page, filter)
            elif isinstance(filter, CustomsOfficeFilter):
                self._apply_customs_office_filter(page, filter)
    
    def _apply_domestic_region_filter(self, page: Page, filter: DomesticRegionFilter):
        """
        국내지역 필터 적용
        
        Args:
            page: Playwright Page 객체
            filter: DomesticRegionFilter 객체
        """
        print(f"  [7] Selecting '국내지역' filter")
        print(f"  [8] Selecting scope from dropdown: '{filter.scope}'")
        
        for region in filter.regions:
            print(f"  [9] Selecting region from dropdown: '{region}'")
        
        print(f"  [10] Clicking '조회하기' button")
    
    def _apply_customs_office_filter(self, page: Page, filter: CustomsOfficeFilter):
        """
        세관 필터 적용
        
        Args:
            page: Playwright Page 객체
            filter: CustomsOfficeFilter 객체
        """
        print(f"  [7] Selecting '세관' filter")
        
        for customs in filter.customs_offices:
            print(f"  [8-9] Selecting customs office from dropdown: '{customs}'")
        
        print(f"  [10] Clicking '조회하기' button")
    
    def _download_data(self, page: Page, save_dir: str, strategy_name: str, item_name: str) -> str:
        """
        데이터 다운로드 (11-13단계)
        
        Args:
            page: Playwright Page 객체
            save_dir: 저장 디렉토리
            strategy_name: 전략 이름
            item_name: 품목 이름
            
        Returns:
            다운로드된 파일 경로
        """
        print(f"  [11] Clicking first row's export amount cell")
        print(f"  [12] Clicking download button")
        print(f"  [13] Accepting download alert")
        
        # 가상의 파일 경로 반환 (테스트용)
        file_path = f"{save_dir}/{strategy_name}_{item_name}.xlsx"
        print(f"  → Downloaded: {file_path}")
        
        return file_path
