"""
HTML 파싱 유닛 테스트

실제 HTML 파일들에 대한 BeautifulSoup selector 로직을 검증합니다.
각 단계별로 필요한 요소들이 올바르게 선택되는지 테스트합니다.
"""

import unittest
import os
from bs4 import BeautifulSoup


class TestHTMLParsing(unittest.TestCase):
    """HTML 파싱 테스트"""
    
    def setUp(self):
        """테스트 준비"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "data"))
    
    def _load_html(self, filename: str) -> BeautifulSoup:
        """HTML 파일 로드"""
        html_path = os.path.join(self.data_dir, filename)
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return BeautifulSoup(html_content, 'html.parser')
    
    def test_bandtrass_search_page(self):
        """메인 검색 페이지 파싱 테스트"""
        soup = self._load_html("bandtrass_search.html")
        
        # 품목/성질별 버튼
        goods_div = soup.find('div', {'id': 'GODS_DIV'})
        self.assertIsNotNone(goods_div, "품목/성질별 버튼을 찾을 수 없습니다")
        self.assertIn("품목/성질별", goods_div.text)
        
        # 국내지역 버튼
        location_div = soup.find('div', {'id': 'LOCATION_DIV'})
        self.assertIsNotNone(location_div, "국내지역 버튼을 찾을 수 없습니다")
        self.assertIn("국내지역", location_div.text)
        
        # 조회하기 버튼 (onclick="javascript:goSearch(); return false;" 속성으로 찾기)
        search_button = soup.find('button', {'onclick': lambda x: x and 'goSearch' in x})
        self.assertIsNotNone(search_button, "조회하기 버튼을 찾을 수 없습니다")
        self.assertIn("조회하기", search_button.get_text())
        
        print("\n[OK] 메인 검색 페이지 요소 확인 완료")
    
    def test_hscode_popup(self):
        """HS Code 팝업 파싱 테스트"""
        soup = self._load_html("hscode_popup.html")
        
        # 직접입력 텍스트 필드
        custom_text = soup.find('input', {'id': 'CustomText'})
        self.assertIsNotNone(custom_text, "HS Code 입력 필드를 찾을 수 없습니다")
        
        # 직접입력추가 버튼
        custom_button = soup.find('button', {'id': 'CustomCheck'})
        self.assertIsNotNone(custom_button, "직접입력추가 버튼을 찾을 수 없습니다")
        self.assertIn("직접입력추가", custom_button.text)
        
        # 선택적용 버튼
        ok_button = soup.find('button', {'onclick': 'fn_ok();'})
        self.assertIsNotNone(ok_button, "선택적용 버튼을 찾을 수 없습니다")
        self.assertIn("선택적용", ok_button.text)
        
        # 선택한 HSCODE 테이블
        select_tbody = soup.find('tbody', {'id': 'tbody_Select'})
        self.assertIsNotNone(select_tbody, "선택한 HSCODE 테이블 body를 찾을 수 없습니다")
        
        print("\n[OK] HS Code 팝업 요소 확인 완료")
    
    def test_goods_type_selected(self):
        """품목/성질별 선택 후 페이지 파싱 테스트"""
        soup = self._load_html("goods_type_selected.html")
        
        # 드롭다운에서 선택된 값 확인 (GODS_TYPE)
        dropdown = soup.find('select', {'id': 'GODS_TYPE'})
        self.assertIsNotNone(dropdown, "품목 드롭다운을 찾을 수 없습니다")
        
        # 옵션들 확인
        options = dropdown.find_all('option')
        self.assertGreater(len(options), 0, "드롭다운 옵션이 없습니다")
        
        # 검색하기 버튼 확인
        popup_button = soup.find('span', {'id': 'POPUP1'})
        self.assertIsNotNone(popup_button, "검색하기 버튼을 찾을 수 없습니다")
        self.assertIn("검색하기", popup_button.text)
        
        print(f"\n[OK] 품목/성질별 선택 완료 - 드롭다운 옵션 수: {len(options)}")
    
    def test_location_filter_clicked(self):
        """국내지역 필터 클릭 후 페이지 파싱 테스트"""
        soup = self._load_html("location_filter_clicked.html")
        
        # 시군구 선택 드롭다운
        location_type = soup.find('select', {'id': 'LOCATION_TYPE'})
        self.assertIsNotNone(location_type, "시군구 선택 드롭다운을 찾을 수 없습니다")
        
        # 옵션 확인
        options = location_type.find_all('option')
        self.assertGreater(len(options), 0, "드롭다운 옵션이 없습니다")
        
        # "시 선택"과 "시군구 선택" 옵션 확인
        option_values = [opt.get('value') for opt in options]
        self.assertIn('A', option_values, "시 선택 옵션이 없습니다")
        self.assertIn('B', option_values, "시군구 선택 옵션이 없습니다")
        
        print("\n[OK] 국내지역 필터 클릭 후 요소 확인 완료")
    
    def test_region_selected(self):
        """지역 선택 후 페이지 파싱 테스트"""
        soup = self._load_html("region_selected.html")
        
        # multiselect 드롭다운
        select_element = soup.find('select', {'id': 'Select2'})
        self.assertIsNotNone(select_element, "multiselect 드롭다운을 찾을 수 없습니다")
        self.assertEqual(select_element.get('multiple'), 'multiple', "multiple 속성이 없습니다")
        
        # 옵션 그룹 확인
        optgroups = select_element.find_all('optgroup')
        self.assertGreater(len(optgroups), 0, "optgroup이 없습니다")
        
        # 첫 번째 optgroup 확인 (서울)
        seoul_group = optgroups[0]
        self.assertEqual(seoul_group.get('label'), '서울', "첫 번째 optgroup이 서울이 아닙니다")
        
        # 서울 내 옵션 확인
        seoul_options = seoul_group.find_all('option')
        self.assertGreater(len(seoul_options), 0, "서울 옵션이 없습니다")
        
        # 선택된 지역 표시 확인
        selected_region_kor = soup.find('p', {'id': 'FILTER2_KOR'})
        self.assertIsNotNone(selected_region_kor, "선택된 지역 표시(한글)를 찾을 수 없습니다")
        
        selected_region_code = soup.find('p', {'id': 'FILTER2_CODE'})
        self.assertIsNotNone(selected_region_code, "선택된 지역 표시(코드)를 찾을 수 없습니다")
        
        print(f"\n[OK] 지역 선택 완료 - 한글: {selected_region_kor.text}, 코드: {selected_region_code.text}")
    
    def test_goods_filter_clicked(self):
        """품목필터 클릭 후 페이지 파싱 테스트"""
        soup = self._load_html("goods_filter_clicked.html")
        
        # GODS_TYPE 드롭다운 확인
        goods_type = soup.find('select', {'id': 'GODS_TYPE'})
        self.assertIsNotNone(goods_type, "GODS_TYPE 드롭다운을 찾을 수 없습니다")
        
        # 옵션들 확인
        options = goods_type.find_all('option')
        option_texts = [opt.text for opt in options]
        self.assertIn("품목", option_texts, "품목 옵션이 없습니다")
        self.assertIn("성질별", option_texts, "성질별 옵션이 없습니다")
        
        print(f"\n[OK] 품목필터 클릭 후 - 옵션: {', '.join(option_texts)}")
    
    def test_workflow_sequence(self):
        """전체 워크플로우 시퀀스 테스트"""
        print("\n" + "="*60)
        print("전체 워크플로우 시퀀스 검증")
        print("="*60)
        
        # 1. 메인 페이지
        main_soup = self._load_html("bandtrass_search.html")
        print("\n[1] 메인 검색 페이지 로드 [OK]")
        
        # 2. 품목/성질별 선택
        goods_soup = self._load_html("goods_type_selected.html")
        dropdown = goods_soup.find('select', {'id': 'GODS_TYPE'})
        self.assertIsNotNone(dropdown)
        print("[2] 품목/성질별 드롭다운 선택 [OK]")
        
        # 3. HS Code 팝업
        hscode_soup = self._load_html("hscode_popup.html")
        custom_text = hscode_soup.find('input', {'id': 'CustomText'})
        custom_button = hscode_soup.find('button', {'id': 'CustomCheck'})
        ok_button = hscode_soup.find('button', {'onclick': 'fn_ok();'})
        self.assertIsNotNone(custom_text)
        self.assertIsNotNone(custom_button)
        self.assertIsNotNone(ok_button)
        print("[3] HS Code 검색하기 클릭 [OK]")
        print("[4] HS Code 입력 필드 확인 [OK]")
        print("[5] 직접입력추가 버튼 확인 [OK]")
        print("[6] 선택적용 버튼 확인 [OK]")
        
        # 4. 필터 선택
        filter_soup = self._load_html("location_filter_clicked.html")
        location_type = filter_soup.find('select', {'id': 'LOCATION_TYPE'})
        self.assertIsNotNone(location_type)
        print("[7] 필터 선택 (국내지역) [OK]")
        print("[8] Scope 선택 (시군구) [OK]")
        
        # 5. 지역 선택
        region_soup = self._load_html("region_selected.html")
        select_element = region_soup.find('select', {'id': 'Select2'})
        self.assertIsNotNone(select_element)
        print("[9] 지역 선택 완료 [OK]")
        
        print("\n" + "="*60)
        print("모든 워크플로우 단계 검증 완료!")
        print("="*60)


if __name__ == '__main__':
    unittest.main(verbosity=2)
