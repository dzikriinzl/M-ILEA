"""
Research Metrics Module

Provides evaluation metrics for research paper:
- Precision, Recall, F1-Score
- True Positives, False Positives, False Negatives
- Comparison metrics across tools
- Statistical analysis

Reference: ARAP paper evaluation methodology
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
import logging
import math

logger = logging.getLogger(__name__)


@dataclass
class ConfusionMatrix:
    """Confusion matrix for binary classification"""
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    
    @property
    def total(self) -> int:
        return self.true_positives + self.false_positives + self.true_negatives + self.false_negatives
    
    @property
    def accuracy(self) -> float:
        """Accuracy: (TP + TN) / Total"""
        if self.total == 0:
            return 0.0
        return (self.true_positives + self.true_negatives) / self.total
    
    @property
    def precision(self) -> float:
        """Precision: TP / (TP + FP)"""
        denom = self.true_positives + self.false_positives
        if denom == 0:
            return 0.0
        return self.true_positives / denom
    
    @property
    def recall(self) -> float:
        """Recall (Sensitivity): TP / (TP + FN)"""
        denom = self.true_positives + self.false_negatives
        if denom == 0:
            return 0.0
        return self.true_positives / denom
    
    @property
    def f1_score(self) -> float:
        """F1 Score: 2 * (Precision * Recall) / (Precision + Recall)"""
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)
    
    @property
    def specificity(self) -> float:
        """Specificity: TN / (TN + FP)"""
        denom = self.true_negatives + self.false_positives
        if denom == 0:
            return 0.0
        return self.true_negatives / denom
    
    @property
    def fpr(self) -> float:
        """False Positive Rate: FP / (FP + TN)"""
        denom = self.false_positives + self.true_negatives
        if denom == 0:
            return 0.0
        return self.false_positives / denom


@dataclass
class DetectionMetrics:
    """Metrics for detection accuracy"""
    total_expected: int              # From ground truth
    total_detected: int              # By tool
    correctly_detected: int          # True positives
    missed_detections: int           # False negatives
    false_positives: int             # Extra detections
    
    @property
    def precision(self) -> float:
        """Precision: Correctly Detected / Total Detected"""
        if self.total_detected == 0:
            return 0.0
        return self.correctly_detected / self.total_detected
    
    @property
    def recall(self) -> float:
        """Recall: Correctly Detected / Total Expected"""
        if self.total_expected == 0:
            return 0.0
        return self.correctly_detected / self.total_expected
    
    @property
    def f1_score(self) -> float:
        """F1 Score"""
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)


@dataclass
class ConfidenceMetrics:
    """Metrics for confidence score quality"""
    mean_confidence: float           # Average confidence
    median_confidence: float         # Median confidence
    std_confidence: float            # Standard deviation
    min_confidence: float            # Minimum
    max_confidence: float            # Maximum
    
    confidence_distribution: Dict[str, int]  # {range: count}
    # Ranges: "0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"


class MetricsCalculator:
    """Calculate evaluation metrics"""
    
    @staticmethod
    def calculate_detection_metrics(ground_truth: Set[str], 
                                   detected: Set[str]) -> DetectionMetrics:
        """
        Calculate detection metrics.
        
        Args:
            ground_truth: Set of expected findings (fingerprints)
            detected: Set of detected findings (fingerprints)
        
        Returns:
            DetectionMetrics with precision, recall, F1
        """
        
        correctly_detected = len(ground_truth & detected)
        missed = len(ground_truth - detected)
        false_pos = len(detected - ground_truth)
        
        return DetectionMetrics(
            total_expected=len(ground_truth),
            total_detected=len(detected),
            correctly_detected=correctly_detected,
            missed_detections=missed,
            false_positives=false_pos
        )
    
    @staticmethod
    def calculate_confidence_metrics(confidences: List[float]) -> ConfidenceMetrics:
        """
        Calculate confidence score metrics.
        
        Args:
            confidences: List of confidence scores [0.0-1.0]
        
        Returns:
            ConfidenceMetrics
        """
        
        if not confidences:
            return ConfidenceMetrics(
                mean_confidence=0.0,
                median_confidence=0.0,
                std_confidence=0.0,
                min_confidence=0.0,
                max_confidence=0.0,
                confidence_distribution={}
            )
        
        # Sort for median
        sorted_conf = sorted(confidences)
        n = len(sorted_conf)
        
        # Mean
        mean = sum(confidences) / n
        
        # Median
        if n % 2 == 0:
            median = (sorted_conf[n//2 - 1] + sorted_conf[n//2]) / 2
        else:
            median = sorted_conf[n//2]
        
        # Standard deviation
        variance = sum((c - mean) ** 2 for c in confidences) / n
        std = math.sqrt(variance)
        
        # Min/Max
        min_conf = min(confidences)
        max_conf = max(confidences)
        
        # Distribution
        distribution = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0,
        }
        
        for conf in confidences:
            if conf < 0.2:
                distribution["0.0-0.2"] += 1
            elif conf < 0.4:
                distribution["0.2-0.4"] += 1
            elif conf < 0.6:
                distribution["0.4-0.6"] += 1
            elif conf < 0.8:
                distribution["0.6-0.8"] += 1
            else:
                distribution["0.8-1.0"] += 1
        
        return ConfidenceMetrics(
            mean_confidence=round(mean, 3),
            median_confidence=round(median, 3),
            std_confidence=round(std, 3),
            min_confidence=round(min_conf, 3),
            max_confidence=round(max_conf, 3),
            confidence_distribution=distribution
        )
    
    @staticmethod
    def calculate_complexity_metrics(findings: List) -> Dict:
        """
        Calculate detection complexity metrics.
        
        How many findings involve:
        - Multiple factors (API + string + logic)
        - Multiple layers (Java + Native)
        - Complex control flow
        """
        
        multi_factor = 0
        multi_layer = 0
        complex_flow = 0
        total = len(findings)
        
        for f in findings:
            breakdown = getattr(f, 'confidence_breakdown', {})
            
            # Count factors
            factors_found = breakdown.get('factors_found', 0)
            if factors_found >= 3:
                multi_factor += 1
            
            # Check for native layer
            if breakdown.get('native_layer', False):
                multi_layer += 1
            
            # Check for control flow
            if breakdown.get('control_flow', False):
                complex_flow += 1
        
        return {
            "multi_factor_count": multi_factor,
            "multi_factor_percent": (multi_factor / total * 100) if total > 0 else 0,
            "multi_layer_count": multi_layer,
            "multi_layer_percent": (multi_layer / total * 100) if total > 0 else 0,
            "complex_flow_count": complex_flow,
            "complex_flow_percent": (complex_flow / total * 100) if total > 0 else 0,
        }


class ComparisonMetricsGenerator:
    """
    Generate comparison metrics across tools/versions.
    
    For paper: ILEA v1 vs ILEA v2 vs MobSF vs Ground Truth
    """
    
    @staticmethod
    def generate_tool_comparison(
        ground_truth_findings: Dict[str, List],
        ilea_v1_findings: Dict[str, List],
        ilea_v2_findings: Dict[str, List],
        mobsf_findings: Dict[str, List] = None
    ) -> Dict:
        """
        Generate comprehensive comparison across tools.
        
        Args:
            ground_truth_findings: {app_name: [finding_fingerprints]}
            ilea_v1_findings: ILEA v1 detections
            ilea_v2_findings: ILEA v2 detections
            mobsf_findings: MobSF detections (optional)
        
        Returns:
            Comparison metrics for paper
        """
        
        results = {}
        
        for app_name, ground_truth in ground_truth_findings.items():
            gt_set = set(ground_truth)
            v1_set = set(ilea_v1_findings.get(app_name, []))
            v2_set = set(ilea_v2_findings.get(app_name, []))
            mobsf_set = set(mobsf_findings.get(app_name, [])) if mobsf_findings else set()
            
            # Calculate metrics
            v1_metrics = MetricsCalculator.calculate_detection_metrics(gt_set, v1_set)
            v2_metrics = MetricsCalculator.calculate_detection_metrics(gt_set, v2_set)
            mobsf_metrics = MetricsCalculator.calculate_detection_metrics(gt_set, mobsf_set) if mobsf_set else None
            
            results[app_name] = {
                "ground_truth": len(gt_set),
                "ilea_v1": {
                    "detected": v1_metrics.total_detected,
                    "correct": v1_metrics.correctly_detected,
                    "precision": round(v1_metrics.precision, 3),
                    "recall": round(v1_metrics.recall, 3),
                    "f1": round(v1_metrics.f1_score, 3),
                },
                "ilea_v2": {
                    "detected": v2_metrics.total_detected,
                    "correct": v2_metrics.correctly_detected,
                    "precision": round(v2_metrics.precision, 3),
                    "recall": round(v2_metrics.recall, 3),
                    "f1": round(v2_metrics.f1_score, 3),
                },
            }
            
            if mobsf_metrics:
                results[app_name]["mobsf"] = {
                    "detected": mobsf_metrics.total_detected,
                    "correct": mobsf_metrics.correctly_detected,
                    "precision": round(mobsf_metrics.precision, 3),
                    "recall": round(mobsf_metrics.recall, 3),
                    "f1": round(mobsf_metrics.f1_score, 3),
                }
        
        return results
    
    @staticmethod
    def generate_improvement_summary(comparison: Dict) -> Dict:
        """
        Generate summary of improvements from v1 to v2.
        
        For paper abstract/results section.
        """
        
        total_apps = len(comparison)
        
        improvements = {
            "precision_improved": 0,
            "recall_improved": 0,
            "f1_improved": 0,
            "avg_precision_gain": 0.0,
            "avg_recall_gain": 0.0,
            "avg_f1_gain": 0.0,
        }
        
        precision_gains = []
        recall_gains = []
        f1_gains = []
        
        for app_name, metrics in comparison.items():
            v1 = metrics.get("ilea_v1", {})
            v2 = metrics.get("ilea_v2", {})
            
            if not v1 or not v2:
                continue
            
            # Precision
            p_gain = v2.get("precision", 0) - v1.get("precision", 0)
            if p_gain > 0:
                improvements["precision_improved"] += 1
            precision_gains.append(p_gain)
            
            # Recall
            r_gain = v2.get("recall", 0) - v1.get("recall", 0)
            if r_gain > 0:
                improvements["recall_improved"] += 1
            recall_gains.append(r_gain)
            
            # F1
            f1_gain = v2.get("f1", 0) - v1.get("f1", 0)
            if f1_gain > 0:
                improvements["f1_improved"] += 1
            f1_gains.append(f1_gain)
        
        # Calculate averages
        if precision_gains:
            improvements["avg_precision_gain"] = round(sum(precision_gains) / len(precision_gains), 3)
        if recall_gains:
            improvements["avg_recall_gain"] = round(sum(recall_gains) / len(recall_gains), 3)
        if f1_gains:
            improvements["avg_f1_gain"] = round(sum(f1_gains) / len(f1_gains), 3)
        
        improvements["total_apps"] = total_apps
        
        return improvements


class ResearchMetricsReporter:
    """
    Generate final research-grade metrics report.
    
    Ready for insertion into research paper.
    """
    
    @staticmethod
    def generate_paper_report(
        evaluation_results: Dict,
        app_scores: List = None,
        vulnerabilities_found: int = 0
    ) -> str:
        """
        Generate markdown report for paper inclusion.
        """
        
        report = """
# Research Evaluation Results

## Summary

"""
        
        # Add evaluation metrics
        if evaluation_results:
            report += "\n## Detection Accuracy Metrics\n\n"
            report += "| App | GT | ILEAv1 | Prec | Recall | F1 | ILEAv2 | Prec | Recall | F1 |\n"
            report += "|-----|----|----|----|----|----|----|----|----|----|\n"
            
            for app_name, metrics in evaluation_results.items():
                gt = metrics.get("ground_truth", 0)
                v1 = metrics.get("ilea_v1", {})
                v2 = metrics.get("ilea_v2", {})
                
                report += f"| {app_name} | {gt} | "
                report += f"{v1.get('detected', 0)} | "
                report += f"{v1.get('precision', 0):.2f} | "
                report += f"{v1.get('recall', 0):.2f} | "
                report += f"{v1.get('f1', 0):.2f} | "
                report += f"{v2.get('detected', 0)} | "
                report += f"{v2.get('precision', 0):.2f} | "
                report += f"{v2.get('recall', 0):.2f} | "
                report += f"{v2.get('f1', 0):.2f} |\n"
        
        # Add app scores
        if app_scores:
            report += "\n## Application Security Posture\n\n"
            report += "| App | Findings | Avg Conf | Sophistication | Tier |\n"
            report += "|-----|----------|----------|---|---|\n"
            
            for score in app_scores:
                report += f"| {score.app_name} | {score.total_findings} | "
                report += f"{score.avg_confidence:.2f} | "
                report += f"{score.sophistication_score:.2f} | "
                report += f"{score.overall_tier} |\n"
        
        # Add vulnerability info
        if vulnerabilities_found > 0:
            report += f"\n## Vulnerability Analysis\n\n"
            report += f"**Total Vulnerabilities Detected**: {vulnerabilities_found}\n\n"
        
        return report
