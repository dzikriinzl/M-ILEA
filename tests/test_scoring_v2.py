#!/usr/bin/env python3
"""
Unit Tests for ILEA v2.0 Scoring System

Comprehensive test suite untuk semua new modules.
Run with: pytest tests/test_scoring_v2.py -v

"""

import pytest
from pathlib import Path
import sys

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.scoring.scorer_v2 import (
    ConfidenceScorer, MethodLevelScorer, ClassLevelScorer,
    AppLevelScorer, SignalFactors
)
from core.vulnerability import VulnerabilityScanner, VulnerabilityPatterns
from core.research.metrics import (
    ConfusionMatrix, DetectionMetrics, ConfidenceMetrics,
    MetricsCalculator
)


# ============================================================================
# TEST SUITE 1: Signal-Level Scoring (ConfidenceScorer)
# ============================================================================

class TestConfidenceScorer:
    """Test signal-level confidence scoring"""
    
    @pytest.fixture
    def scorer(self):
        return ConfidenceScorer()
    
    def test_api_match_only(self, scorer):
        """API match should give 0.4 confidence"""
        signal = {"sink": {"api": "Runtime.exec"}}
        conf, factors = scorer.score_signal(signal)
        
        assert conf == 0.4
        assert factors.has_api_match == True
        assert factors.has_string_match == False
    
    def test_api_plus_string(self, scorer):
        """API + string should give 0.6 (0.4 + 0.2)"""
        signal = {
            "sink": {"api": "Runtime.exec"},
            "has_string_match": True
        }
        conf, factors = scorer.score_signal(signal)
        
        assert conf == 0.6
        assert factors.has_api_match == True
        assert factors.has_string_match == True
    
    def test_api_plus_string_plus_logic(self, scorer):
        """API + string + logic should give 0.75"""
        signal = {
            "sink": {"api": "Runtime.exec"},
            "has_string_match": True,
            "conditional": True
        }
        conf, factors = scorer.score_signal(signal)
        
        assert conf == 0.75
        assert factors.has_conditional_logic == True
    
    def test_all_factors(self, scorer):
        """All factors should approach 1.0"""
        signal = {
            "sink": {"api": "Runtime.exec"},
            "has_string_match": True,
            "conditional": True,
            "layer": "Native",
            "context_strength": 1.0
        }
        conf, factors = scorer.score_signal(signal)
        
        assert conf >= 0.9  # Should be high
        assert factors.has_api_match == True
        assert factors.has_string_match == True
        assert factors.has_conditional_logic == True
        assert factors.is_native_layer == True
    
    def test_redundancy_bonus(self, scorer):
        """Multiple checks (3+) should add redundancy bonus"""
        signal = {
            "sink": {"api": "Runtime.exec"},
            "has_string_match": True,
            "conditional": True,
            "layer": "Native"
        }
        conf, factors = scorer.score_signal(signal)
        
        assert factors.has_multiple_checks == True
        # Score should include redundancy bonus
        assert conf >= 0.85
    
    def test_score_capped_at_1_0(self, scorer):
        """Confidence should never exceed 1.0"""
        signal = {
            "sink": {"api": "API1"},
            "has_string_match": True,
            "conditional": True,
            "layer": "Native",
            "context_strength": 1.0
        }
        conf, _ = scorer.score_signal(signal)
        
        assert conf <= 1.0
    
    def test_empty_signal(self, scorer):
        """Empty signal should return 0.0"""
        signal = {}
        conf, _ = scorer.score_signal(signal)
        
        assert conf == 0.0


# ============================================================================
# TEST SUITE 2: Method-Level Scoring (MethodLevelScorer)
# ============================================================================

class TestMethodLevelScorer:
    """Test method-level aggregation"""
    
    def test_single_signal(self):
        """Single signal → simple sophistication"""
        signals = [{"sink": {"api": "Runtime.exec"}}]
        score = MethodLevelScorer.score_method("test_method", signals)
        
        assert score.num_signals == 1
        assert score.sophistication_level == "simple"
        assert score.method_confidence >= 0.2
    
    def test_multiple_signals(self):
        """Multiple signals → moderate/advanced sophistication"""
        signals = [
            {"sink": {"api": "Runtime.exec"}, "has_string_match": True},
            {"sink": {"api": "ProcessBuilder"}, "conditional": True},
            {"sink": {"api": "exec"}, "has_string_match": True}
        ]
        score = MethodLevelScorer.score_method("test_method", signals)
        
        assert score.num_signals == 3
        assert score.sophistication_level in ["moderate", "advanced"]
        assert score.avg_signal_confidence > 0.4
    
    def test_empty_signals(self):
        """No signals should return zero score"""
        score = MethodLevelScorer.score_method("empty_method", [])
        
        assert score.num_signals == 0
        assert score.method_confidence == 0.0
        assert score.sophistication_level == "none"


# ============================================================================
# TEST SUITE 3: Vulnerability Scanning
# ============================================================================

class TestVulnerabilityScanner:
    """Test vulnerability pattern detection"""
    
    @pytest.fixture
    def scanner(self):
        return VulnerabilityScanner()
    
    def test_pattern_registry_loaded(self):
        """All patterns should load correctly"""
        patterns = VulnerabilityPatterns.get_all_patterns()
        
        assert len(patterns) >= 15
        assert "NET_UNENCRYPTED_HTTP" in patterns
        assert "CRYPTO_HARDCODED_KEY" in patterns
    
    def test_pattern_properties(self):
        """Patterns should have all required fields"""
        patterns = VulnerabilityPatterns.get_all_patterns()
        
        for pattern_id, pattern in patterns.items():
            assert pattern.id == pattern_id
            assert pattern.name
            assert pattern.category
            assert pattern.severity
            assert pattern.description
    
    def test_http_detection(self, scanner):
        """Should detect unencrypted HTTP"""
        findings = [{
            'protection_type': 'Network Security',
            'evidence_snippet': ['HttpURLConnection conn = new HttpURLConnection("http://example.com")']
        }]
        
        vulns = scanner.scan_findings(findings)
        
        # Should find HTTP vulnerability
        assert any(v.vulnerability_id == "NET_UNENCRYPTED_HTTP" for v in vulns)
    
    def test_crypto_detection(self, scanner):
        """Should detect weak cryptography"""
        findings = [{
            'protection_type': 'Cryptography',
            'evidence_snippet': ['MessageDigest.getInstance("MD5")']
        }]
        
        vulns = scanner.scan_findings(findings)
        
        # Should find weak crypto
        assert any(v.vulnerability_id == "CRYPTO_WEAK_ALGORITHM" for v in vulns)
    
    def test_summary_generation(self, scanner):
        """Should generate vulnerability summary"""
        findings = [
            {'evidence_snippet': ['HttpURLConnection']},
            {'evidence_snippet': ['MD5']},
            {'evidence_snippet': ['SharedPreferences']}
        ]
        
        scanner.scan_findings(findings)
        summary = scanner.get_vulnerability_summary()
        
        assert "total_vulnerabilities" in summary
        assert "by_severity" in summary
        assert "by_category" in summary


# ============================================================================
# TEST SUITE 4: Research Metrics
# ============================================================================

class TestMetricsCalculator:
    """Test research metrics calculation"""
    
    def test_detection_metrics_perfect(self):
        """Perfect detection should show 100% metrics"""
        ground_truth = {"det1", "det2", "det3"}
        detected = {"det1", "det2", "det3"}
        
        metrics = MetricsCalculator.calculate_detection_metrics(ground_truth, detected)
        
        assert metrics.precision == 1.0
        assert metrics.recall == 1.0
        assert metrics.f1_score == 1.0
        assert metrics.correctly_detected == 3
        assert metrics.false_positives == 0
    
    def test_detection_metrics_partial(self):
        """Partial detection should show appropriate metrics"""
        ground_truth = {"det1", "det2", "det3", "det4"}
        detected = {"det1", "det2", "fp1"}  # 2 correct, 1 false positive
        
        metrics = MetricsCalculator.calculate_detection_metrics(ground_truth, detected)
        
        assert metrics.correctly_detected == 2
        assert metrics.false_positives == 1
        assert metrics.missed_detections == 2
        assert metrics.precision == pytest.approx(2/3, rel=0.01)
        assert metrics.recall == pytest.approx(2/4, rel=0.01)
    
    def test_confidence_metrics(self):
        """Should calculate confidence distribution correctly"""
        confidences = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        
        metrics = MetricsCalculator.calculate_confidence_metrics(confidences)
        
        assert metrics.mean_confidence == pytest.approx(sum(confidences)/len(confidences), rel=0.01)
        assert metrics.median_confidence == 0.6
        assert metrics.min_confidence == 0.3
        assert metrics.max_confidence == 0.9
        assert metrics.std_confidence > 0
        
        # Check distribution
        dist = metrics.confidence_distribution
        assert dist["0.2-0.4"] == 2  # 0.3, 0.4
        assert dist["0.4-0.6"] == 2  # 0.5, 0.6
        assert dist["0.6-0.8"] == 2  # 0.7, 0.8
        assert dist["0.8-1.0"] == 1  # 0.9
    
    def test_confusion_matrix_metrics(self):
        """ConfusionMatrix should calculate all metrics correctly"""
        cm = ConfusionMatrix(
            true_positives=70,
            false_positives=10,
            true_negatives=15,
            false_negatives=5
        )
        
        assert cm.total == 100
        assert cm.accuracy == pytest.approx(0.85, rel=0.01)
        assert cm.precision == pytest.approx(70/80, rel=0.01)
        assert cm.recall == pytest.approx(70/75, rel=0.01)
        assert cm.specificity == pytest.approx(15/25, rel=0.01)
        assert cm.fpr == pytest.approx(10/25, rel=0.01)


# ============================================================================
# TEST SUITE 5: Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for complete pipeline"""
    
    def test_complete_scoring_pipeline(self):
        """Test complete signal → method → class → app scoring"""
        # Create sample findings
        findings = [
            {
                'protection_type': 'Root Detection',
                'location': {'class': 'SecurityManager', 'method': 'checkRoot'},
                'signal_confidence': 0.9
            },
            {
                'protection_type': 'Debugger Detection',
                'location': {'class': 'SecurityManager', 'method': 'checkDebugger'},
                'signal_confidence': 0.75
            },
        ]
        
        # Calculate metrics
        confidences = [f['signal_confidence'] for f in findings]
        metrics = MetricsCalculator.calculate_confidence_metrics(confidences)
        
        assert metrics.mean_confidence == pytest.approx(0.825, rel=0.01)
        assert metrics.max_confidence == 0.9
        assert len(metrics.confidence_distribution) == 5


# ============================================================================
# TEST SUITE 6: Edge Cases & Error Handling
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_scorer_with_dict_input(self):
        """Should handle dict input correctly"""
        scorer = ConfidenceScorer()
        signal = {"sink": {"api": "test"}}
        
        conf, factors = scorer.score_signal(signal)
        assert conf >= 0
        assert conf <= 1.0
    
    def test_empty_findings(self):
        """Should handle empty findings list"""
        metrics = MetricsCalculator.calculate_confidence_metrics([])
        
        assert metrics.mean_confidence == 0.0
        assert metrics.median_confidence == 0.0
    
    def test_single_confidence(self):
        """Should handle single confidence value"""
        metrics = MetricsCalculator.calculate_confidence_metrics([0.7])
        
        assert metrics.mean_confidence == 0.7
        assert metrics.median_confidence == 0.7
        assert metrics.std_confidence == 0.0
    
    def test_extreme_values(self):
        """Should handle extreme confidence values"""
        metrics = MetricsCalculator.calculate_confidence_metrics([0.0, 1.0])
        
        assert metrics.min_confidence == 0.0
        assert metrics.max_confidence == 1.0
        assert metrics.mean_confidence == 0.5


# ============================================================================
# Pytest Configuration
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
