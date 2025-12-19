"""
Tests for domain models

테스트 목적:
1. Pydantic 모델의 불변성 검증
2. 데이터 검증 규칙 확인 (음수 방지, 날짜 형식 등)
3. 모델 생성 및 직렬화 테스트
"""

import unittest
from pydantic import ValidationError
from src.domain.models import TradeRecord, AnalysisResult, BusinessMetrics


class TestTradeRecord(unittest.TestCase):
    """TradeRecord 모델 테스트"""
    
    def test_create_valid_record(self):
        """정상적인 TradeRecord 생성"""
        record = TradeRecord(date="2024-01", export_amount=1000.0)
        
        self.assertEqual(record.date, "2024-01")
        self.assertEqual(record.export_amount, 1000.0)
    
    def test_immutability(self):
        """불변성 테스트: 생성 후 수정 불가"""
        record = TradeRecord(date="2024-01", export_amount=1000.0)
        
        with self.assertRaises(ValidationError):
            record.date = "2024-02"  # 수정 시도
    
    def test_invalid_date_format(self):
        """잘못된 날짜 형식 검증"""
        with self.assertRaises(ValidationError):
            TradeRecord(date="2024/01", export_amount=1000.0)  # 슬래시 사용
        
        with self.assertRaises(ValidationError):
            TradeRecord(date="24-01", export_amount=1000.0)  # 연도 2자리
    
    def test_negative_amount_rejected(self):
        """음수 금액 거부"""
        with self.assertRaises(ValidationError):
            TradeRecord(date="2024-01", export_amount=-100.0)


class TestAnalysisResult(unittest.TestCase):
    """AnalysisResult 모델 테스트"""
    
    def test_create_with_optional_fields(self):
        """선택적 필드(MoM, YoY)가 None일 수 있음"""
        result = AnalysisResult(
            date="2024-01",
            export_amount=1000.0,
            export_mom=None,
            export_yoy=None
        )
        
        self.assertIsNone(result.export_mom)
        self.assertIsNone(result.export_yoy)
    
    def test_create_with_all_fields(self):
        """모든 필드 포함 생성"""
        result = AnalysisResult(
            date="2024-02",
            export_amount=1500.0,
            export_mom=50.0,
            export_yoy=25.0
        )
        
        self.assertEqual(result.export_mom, 50.0)
        self.assertEqual(result.export_yoy, 25.0)
    
    def test_equality(self):
        """같은 값을 가진 두 모델은 동등함"""
        result1 = AnalysisResult(
            date="2024-01",
            export_amount=1000.0,
            export_mom=10.0,
            export_yoy=20.0
        )
        result2 = AnalysisResult(
            date="2024-01",
            export_amount=1000.0,
            export_mom=10.0,
            export_yoy=20.0
        )
        
        self.assertEqual(result1, result2)


class TestBusinessMetrics(unittest.TestCase):
    """BusinessMetrics 모델 테스트"""
    
    def test_create_complete_metrics(self):
        """완전한 비즈니스 메트릭 생성"""
        metrics = BusinessMetrics(
            date="2024-01",
            export_amount=20000.0,
            business_days=20,
            daily_avg=1000.0,
            daily_avg_mom=5.0,
            daily_avg_yoy=15.0
        )
        
        self.assertEqual(metrics.business_days, 20)
        self.assertEqual(metrics.daily_avg, 1000.0)
    
    def test_negative_business_days_rejected(self):
        """음수 영업일수 거부"""
        with self.assertRaises(ValidationError):
            BusinessMetrics(
                date="2024-01",
                export_amount=20000.0,
                business_days=-5,  # 음수
                daily_avg=1000.0
            )
    
    def test_json_serialization(self):
        """JSON 직렬화/역직렬화 테스트"""
        metrics = BusinessMetrics(
            date="2024-01",
            export_amount=20000.0,
            business_days=20,
            daily_avg=1000.0
        )
        
        # 직렬화
        json_data = metrics.model_dump_json()
        self.assertIn("2024-01", json_data)
        
        # 역직렬화
        restored = BusinessMetrics.model_validate_json(json_data)
        self.assertEqual(restored, metrics)


if __name__ == '__main__':
    unittest.main()
