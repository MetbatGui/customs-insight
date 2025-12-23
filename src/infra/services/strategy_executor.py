"""
StrategyExecutor - Strategy 객체 기반 스크래핑 실행 서비스

Strategy 객체를 받아 각 품목을 순회하며 필터를 적용하고 데이터를 다운로드합니다.
"""

import json
from typing import List
from playwright.sync_api import Page
from src.domain.models import Strategy, StrategyItem, DomesticRegionFilter
from .scraping import search_item, apply_filters, download_data


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
    
    BASE_URL = "https://www.bandtrass.or.kr/customs/total.do?command=CUS001View&viewCode=CUS00301"
    
    def execute(self, page: Page, save_dir: str, strategy: Strategy) -> List[str]:
        """
        Strategy 실행
        
        Args:
            page: Playwright Page 객체
            save_dir: 저장 디렉토리
            strategy: Strategy 객체
            
        Returns:
            다운로드된 파일 경로 리스트
        """
        print(f"\n{'='*60}")
        print(f"[StrategyExecutor] Executing Strategy: {strategy.name}")
        print(f"{'='*60}")
        
        # Strategy 세부정보 출력
        strategy_dict = strategy.model_dump()
        print(f"\n[Strategy Details]")
        print(json.dumps(strategy_dict, indent=2, ensure_ascii=False))
        print(f"\n{'='*60}\n")
        
        results = []
        
        for idx, item in enumerate(strategy.items, 1):
            print(f"\n--- Item {idx}/{len(strategy.items)}: {item.name} ---")
            print(f"  HS Code: {item.hs_code}")
            print(f"  Filters: {len(item.filters)} filter(s)")
            
            # 지역 필터를 분리하여 각 지역마다 개별 다운로드
            region_filters = [f for f in item.filters if type(f).__name__ == 'DomesticRegionFilter']
            other_filters = [f for f in item.filters if type(f).__name__ != 'DomesticRegionFilter']
            
            print(f"  → Region filters found: {len(region_filters)}")
            if region_filters:
                print(f"  → Regions in filter: {region_filters[0].regions}")
            
            # 지역 필터가 있고 여러 지역이 있는 경우, 각 지역마다 개별 다운로드
            if region_filters and len(region_filters[0].regions) > 1:
                region_filter = region_filters[0]
                print(f"  → Multiple regions detected: {region_filter.regions}")
                print(f"  → Will download separately for each region")
                
                for region_idx, region in enumerate(region_filter.regions, 1):
                    print(f"\n  === Region {region_idx}/{len(region_filter.regions)}: {region} ===")
                    
                    # 이 지역에 대한 단일 필터 생성
                    single_region_filter = DomesticRegionFilter(
                        scope=region_filter.scope,
                        regions=[region]
                    )
                    print(f"  → Created filter with single region: {single_region_filter.regions}")
                    
                    # 단일 품목+지역 처리
                    filters_to_apply = [single_region_filter] + other_filters
                    filename = f"{strategy.name}_{item.name}_{region}"
                    file_path = self._process_single_item(
                        page, save_dir, item, filters_to_apply, filename
                    )
                    results.append(file_path)
            else:
                # 지역 필터가 없거나 단일 지역인 경우
                filename = f"{strategy.name}_{item.name}"
                file_path = self._process_single_item(
                    page, save_dir, item, item.filters, filename
                )
                results.append(file_path)
        
        print(f"\n{'='*60}")
        print(f"[StrategyExecutor] Completed: {len(results)} files downloaded")
        print(f"{'='*60}\n")
        
        return results
    
    def _process_single_item(
        self, 
        page: Page, 
        save_dir: str, 
        item: StrategyItem,
        filters: list,
        filename: str
    ) -> str:
        """
        단일 품목 처리
        
        Args:
            page: Playwright Page 객체
            save_dir: 저장 디렉토리
            item: 처리할 품목
            filters: 적용할 필터 리스트
            filename: 저장할 파일명
            
        Returns:
            다운로드된 파일 경로
        """
        # 페이지 새로 로드
        print(f"  [Navigation] Loading fresh page...")
        page.goto(self.BASE_URL)
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1000)
        
        # 1-6: 품목 검색
        search_item(page, item.hs_code)
        
        # 7-10: 필터 적용 및 조회
        if filters:
            print(f"  [Note] Applying {len(filters)} filter(s)")
            apply_filters(page, filters)
        else:
            # 필터 없으면 바로 조회
            print("  [Note] No filters to apply, proceeding to search")
            page.locator('button[onclick*="goSearch"]').click()
            page.wait_for_timeout(3000)
        
        # 11-13: 데이터 다운로드
        return download_data(page, save_dir, filename)
