"""
에이피알 전략 시나리오 테스트

기존 HTML 테스트 데이터를 활용하여 에이피알 전략의 전체 워크플로우를 검증합니다.
"""

import unittest
import os
from bs4 import BeautifulSoup


class TestAPRScenario(unittest.TestCase):
    """에이피알 전략 시나리오 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.abspath(os.path.join(current_dir, "..", "data"))
        
        # 에이피알 전략 정보
        self.strategy = {
            "name": "에이피알",
            "items": [
                {
                    "name": "화장품",
                    "hs_code": "3304991000",
                    "filter": {
                        "category": "국내지역",
                        "scope": "시군구",
                        "value": "서울 송파구"
                    }
                },
                {
                    "name": "미용기기",
                    "hs_code": "8543702010",
                    "filter": {
                        "category": "국내지역",
                        "scope": "시군구",
                        "value": "서울 송파구"
                    }
                }
            ]
        }
    
    def _load_html(self, filename: str) -> BeautifulSoup:
        """HTML 파일 로드"""
        html_path = os.path.join(self.data_dir, filename)
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return BeautifulSoup(html_content, 'html.parser')
    
    def test_step1_main_page_load(self):
        """Step 1: 메인 검색 페이지 로드"""
        soup = self._load_html("bandtrass_search.html")
        
        # 품목/성질별 버튼 확인
        goods_div = soup.find('div', {'id': 'GODS_DIV'})
        self.assertIsNotNone(goods_div)
        self.assertIn("품목/성질별", goods_div.text)
        
        print("\n[OK] Step 1: 메인 페이지 로드 성공")
    
    def test_step2_goods_filter_click(self):
        """Step 2-3: 품목/성질별 클릭 및 드롭다운 선택"""
        soup = self._load_html("goods_type_selected.html")
        
        # 품목 드롭다운 확인
        dropdown = soup.find('select', {'id': 'GODS_TYPE'})
        self.assertIsNotNone(dropdown)
        
        # 검색하기 버튼 확인
        popup_button = soup.find('span', {'id': 'POPUP1'})
        self.assertIsNotNone(popup_button)
        self.assertIn("검색하기", popup_button.text)
        
        print("\n[OK] Step 2-3: 품목 드롭다운 및 검색하기 버튼 확인")
    
    def test_step3_hscode_input(self):
        """Step 4-6: HS Code 팝업에서 입력 및 선택"""
        soup = self._load_html("hscode_popup.html")
        
        # HS Code 입력 필드
        custom_text = soup.find('input', {'id': 'CustomText'})
        self.assertIsNotNone(custom_text)
        
        # 직접입력추가 버튼
        custom_button = soup.find('button', {'id': 'CustomCheck'})
        self.assertIsNotNone(custom_button)
        self.assertIn("직접입력추가", custom_button.text)
        
        # 선택적용 버튼
        ok_button = soup.find('button', {'onclick': 'fn_ok();'})
        self.assertIsNotNone(ok_button)
        self.assertIn("선택적용", ok_button.text)
        
        # 선택한 HSCODE 테이블
        select_tbody = soup.find('tbody', {'id': 'tbody_Select'})
        self.assertIsNotNone(select_tbody)
        
        print("\n[OK] Step 4-6: HS Code 입력 및 선택 UI 확인")
        print(f"  - HS Code: {self.strategy['items'][0]['hs_code']} (화장품)")
    
    def test_step4_location_filter(self):
        """Step 7-9: 국내지역 필터 선택"""
        soup = self._load_html("location_filter_clicked.html")
        
        # 시군구 선택 드롭다운
        location_type = soup.find('select', {'id': 'LOCATION_TYPE'})
        self.assertIsNotNone(location_type)
        
        # 시군구 옵션 확인
        options = location_type.find_all('option')
        option_values = [opt.get('value') for opt in options]
        self.assertIn('B', option_values, "시군구 선택 옵션")
        
        print("\n[OK] Step 7-9: 국내지역 필터 선택 UI 확인")
    
    def test_step5_region_selection(self):
        """Step 10: 서울 송파구 선택"""
        soup = self._load_html("region_selected.html")
        
        # multiselect 드롭다운
        select_element = soup.find('select', {'id': 'Select2'})
        self.assertIsNotNone(select_element)
        self.assertEqual(select_element.get('multiple'), 'multiple')
        
        # 서울 optgroup 확인
        optgroups = select_element.find_all('optgroup')
        seoul_group = optgroups[0]
        self.assertEqual(seoul_group.get('label'), '서울')
        
        # 서울 송파구 옵션 확인
        seoul_options = seoul_group.find_all('option')
        option_texts = [opt.text for opt in seoul_options]
        
        # 송파구가 있는지 확인
        songpa_found = any('송파구' in text for text in option_texts)
        self.assertTrue(songpa_found, "서울 송파구 옵션 존재")
        
        # 선택된 지역 표시 확인
        selected_region_kor = soup.find('p', {'id': 'FILTER2_KOR'})
        self.assertIsNotNone(selected_region_kor)
        
        print("\n[OK] Step 10: 서울 송파구 선택 UI 확인")
        print(f"  - 선택값: {selected_region_kor.text}")
    
    def test_step6_search_button(self):
        """Step 11: 조회하기 버튼"""
        soup = self._load_html("bandtrass_search.html")
        
        # 조회하기 버튼
        search_button = soup.find('button', {'onclick': lambda x: x and 'goSearch' in x})
        self.assertIsNotNone(search_button)
        self.assertIn("조회하기", search_button.get_text())
        
        print("\n[OK] Step 11: 조회하기 버튼 확인")
    
    def test_full_workflow_sequence(self):
        """전체 워크플로우 시퀀스 테스트"""
        print("\n" + "="*70)
        print("에이피알 전략 - 전체 워크플로우 시뮬레이션")
        print("="*70)
        
        # 품목 1: 화장품
        print("\n[품목 1: 화장품]")
        print(f"  HS Code: {self.strategy['items'][0]['hs_code']}")
        print(f"  필터: {self.strategy['items'][0]['filter']['value']}")
        
        # Step 1: 메인 페이지
        main_soup = self._load_html("bandtrass_search.html")
        goods_div = main_soup.find('div', {'id': 'GODS_DIV'})
        self.assertIsNotNone(goods_div)
        print("\n  [1] 메인 페이지 로드")
        
        # Step 2-3: 품목 선택
        goods_soup = self._load_html("goods_type_selected.html")
        dropdown = goods_soup.find('select', {'id': 'GODS_TYPE'})
        self.assertIsNotNone(dropdown)
        print("  [2] 품목/성질별 버튼 클릭")
        print("  [3] 드롭다운에서 '품목' 선택")
        
        # Step 4-6: HS Code 입력
        hscode_soup = self._load_html("hscode_popup.html")
        custom_text = hscode_soup.find('input', {'id': 'CustomText'})
        custom_button = hscode_soup.find('button', {'id': 'CustomCheck'})
        ok_button = hscode_soup.find('button', {'onclick': 'fn_ok();'})
        self.assertIsNotNone(custom_text)
        self.assertIsNotNone(custom_button)
        self.assertIsNotNone(ok_button)
        print(f"  [4] 검색하기 클릭 -> HS Code 팝업")
        print(f"  [5] HS Code 입력: {self.strategy['items'][0]['hs_code']}")
        print("  [6] 직접입력추가 클릭")
        print("  [7] 선택적용 클릭")
        
        # Step 7-9: 필터 선택
        filter_soup = self._load_html("location_filter_clicked.html")
        location_type = filter_soup.find('select', {'id': 'LOCATION_TYPE'})
        self.assertIsNotNone(location_type)
        print("  [8] 국내지역 필터 선택")
        print("  [9] 시군구 선택")
        
        # Step 10: 지역 선택
        region_soup = self._load_html("region_selected.html")
        select_element = region_soup.find('select', {'id': 'Select2'})
        self.assertIsNotNone(select_element)
        print("  [10] 서울 송파구 선택")
        
        # Step 11: 조회
        search_button = main_soup.find('button', {'onclick': lambda x: x and 'goSearch' in x})
        self.assertIsNotNone(search_button)
        print("  [11] 조회하기 클릭")
        print("  [12] 다운로드 (화장품 데이터)")
        
        # 품목 2: 미용기기 (동일 과정)
        print("\n[품목 2: 미용기기]")
        print(f"  HS Code: {self.strategy['items'][1]['hs_code']}")
        print(f"  필터: {self.strategy['items'][1]['filter']['value']}")
        print("  [13] 동일 과정 반복...")
        print("  [14] 다운로드 (미용기기 데이터)")
        
        print("\n" + "="*70)
        print("[OK] 전체 워크플로우 시뮬레이션 완료!")
        print("="*70)
        print(f"\n총 {len(self.strategy['items'])}개 품목 처리 완료")
        print("모든 selector가 올바르게 작동함을 확인")


    def test_step7_result_table_click(self):
        """Step 12: 조회 결과 테이블에서 수출 금액 클릭"""
        soup = self._load_html("result_table.html")
        
        # jqGrid 테이블 확인
        table = soup.find('table', {'id': 'table_list_1'})
        self.assertIsNotNone(table)
        
        # 첫 번째 데이터 행 확인
        first_row = soup.find('tr', {'id': '1', 'role': 'row'})
        self.assertIsNotNone(first_row)
        
        # 수출 금액 셀 찾기 (aria-describedby="table_list_1_EX_AMT")
        export_amt_cell = soup.find('td', {'aria-describedby': 'table_list_1_EX_AMT'})
        self.assertIsNotNone(export_amt_cell)
        
        # 클릭 가능한 font 태그 확인
        font_tag = export_amt_cell.find('font')
        self.assertIsNotNone(font_tag)
        self.assertIn('cursor:pointer', font_tag.get('style', ''))
        self.assertIn('63,719,738', font_tag.text)
        
        print("\n[OK] Step 12: 조회 결과 테이블 - 수출 금액 셀 확인")
        print(f"  - 수출 금액: {font_tag.text}")
        print(f"  - 품목: [3304991000] 기초화장용 제품류")
        print(f"  - 지역: 서울 송파구")
    
    def test_step8_download_button(self):
        """Step 13: 다운로드 버튼 클릭"""
        soup = self._load_html("result_table.html")
        
        # 다운로드 버튼 찾기
        download_btn = soup.find('a', {'href': lambda x: x and 'GridtoExcel' in x})
        self.assertIsNotNone(download_btn)
        
        # 버튼 속성 확인
        self.assertIn('btn', download_btn.get('class', []))
        self.assertIn('fa-download', download_btn.find('i').get('class', []))
        self.assertEqual('다운로드 ', download_btn.get('data-original-title'))
        
        print("\n[OK] Step 13: 다운로드 버튼 확인")
        print("  - href: javascript:GridtoExcel()")
        print("  - 아이콘: fa-download")


if __name__ == '__main__':
    unittest.main(verbosity=2)
