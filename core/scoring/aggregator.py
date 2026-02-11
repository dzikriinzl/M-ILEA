"""
Score Aggregator for Multi-Level Confidence System

Provides utilities to aggregate findings into method/class/app level scores.
Used for generating research-quality comparison data for papers.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import asdict, dataclass
from collections import defaultdict
import logging

from .scorer_v2 import (
    ConfidenceScorer, MethodLevelScorer, ClassLevelScorer,
    AppLevelScorer, MethodScore, ClassScore, AppScore
)

logger = logging.getLogger(__name__)


class ScoreAggregator:
    """
    Aggregates findings into multi-level scores.
    
    Pipeline:
    1. Process signals → Signal-level scores (ConfidenceScorer)
    2. Group by method → Method-level scores (MethodLevelScorer)
    3. Group by class → Class-level scores (ClassLevelScorer)
    4. Aggregate app → App-level score (AppLevelScorer)
    """
    
    def __init__(self):
        self.signal_scorer = ConfidenceScorer()
        self.method_scorer = MethodLevelScorer()
        self.class_scorer = ClassLevelScorer()
        self.app_scorer = AppLevelScorer()

    def score_findings(self, findings: List) -> Dict:
        """
        Complete pipeline: Score findings at all levels.
        
        Returns:
            {
                "findings_enhanced": [findings with all scores],
                "method_scores": [MethodScore],
                "class_scores": [ClassScore],
                "app_score": AppScore
            }
        """
        # Step 1: Enhance findings with signal scores
        findings_enhanced = self._score_signals(findings)
        
        # Step 2: Group by class+method
        class_method_map = self._group_by_class_method(findings_enhanced)
        
        # Step 3: Calculate method-level scores
        method_scores = self._calculate_method_scores(class_method_map)
        
        # Step 4: Calculate class-level scores
        class_scores = self._calculate_class_scores(class_method_map, method_scores)
        
        # Step 5: Calculate app-level score
        app_score = self.app_scorer.score_app("Unknown", findings_enhanced)
        
        return {
            "findings_enhanced": findings_enhanced,
            "method_scores": method_scores,
            "class_scores": class_scores,
            "app_score": app_score
        }

    def _score_signals(self, findings: List) -> List:
        """
        Enhance each finding with signal and breakdown.
        """
        for f in findings:
            # Calculate signal confidence
            signal_conf, factors = self.signal_scorer.score_signal(f)
            
            # Add to finding - handle both dict and dataclass
            if isinstance(f, dict):
                f['signal_confidence'] = signal_conf
                f['confidence_breakdown'] = {
                    "api_match": factors.has_api_match,
                    "string_indicator": factors.has_string_match,
                    "control_flow": factors.has_conditional_logic,
                    "native_layer": factors.is_native_layer,
                    "context_strength": factors.context_strength,
                    "multiple_checks": factors.has_multiple_checks,
                    "factors_found": sum([
                        factors.has_api_match,
                        factors.has_string_match,
                        factors.has_conditional_logic,
                        factors.is_native_layer,
                    ])
                }
            else:
                f.signal_confidence = signal_conf
                f.confidence_breakdown = {
                    "api_match": factors.has_api_match,
                    "string_indicator": factors.has_string_match,
                    "control_flow": factors.has_conditional_logic,
                    "native_layer": factors.is_native_layer,
                    "context_strength": factors.context_strength,
                    "multiple_checks": factors.has_multiple_checks,
                    "factors_found": sum([
                        factors.has_api_match,
                        factors.has_string_match,
                        factors.has_conditional_logic,
                        factors.is_native_layer,
                    ])
                }
        
        return findings

    def _group_by_class_method(self, findings: List) -> Dict[str, Dict[str, List]]:
        """
        Group findings by class and method.
        
        Returns:
            {
                "ClassName": {
                    "methodName": [findings],
                    ...
                },
                ...
            }
        """
        groups = defaultdict(lambda: defaultdict(list))
        
        for f in findings:
            # Extract location info
            if isinstance(f, dict):
                loc = f.get('location', {})
            else:
                loc = f.location if isinstance(f.location, dict) else asdict(f.location)
            
            class_name = loc.get('class', 'Unknown')
            method_name = loc.get('method', 'Unknown')
            
            groups[class_name][method_name].append(f)
        
        return dict(groups)

    def _calculate_method_scores(self, class_method_map: Dict) -> List[MethodScore]:
        """
        Calculate method-level scores for all methods.
        """
        method_scores = []
        
        for class_name, methods in class_method_map.items():
            for method_name, findings in methods.items():
                score = self.method_scorer.score_method(method_name, findings)
                
                # Enrich with class info
                score.class_name = class_name
                
                method_scores.append(score)
        
        return method_scores

    def _calculate_class_scores(self, class_method_map: Dict, 
                               method_scores: List[MethodScore]) -> List[ClassScore]:
        """
        Calculate class-level scores.
        """
        class_scores = []
        
        # Group method scores by class
        methods_per_class = defaultdict(list)
        for ms in method_scores:
            if hasattr(ms, 'class_name'):
                methods_per_class[ms.class_name].append(ms)
        
        # Score each class
        for class_name, method_score_list in methods_per_class.items():
            score = self.class_scorer.score_class(class_name, method_score_list)
            class_scores.append(score)
        
        return class_scores

    def export_for_paper(self, aggregated_scores: Dict) -> Dict:
        """
        Format aggregated scores for research paper inclusion.
        
        Generates tables and statistics ready for paper figures/tables.
        """
        app_score = aggregated_scores["app_score"]
        method_scores = aggregated_scores["method_scores"]
        class_scores = aggregated_scores["class_scores"]
        
        return {
            "summary": {
                "app_name": app_score.app_name,
                "total_findings": app_score.total_findings,
                "avg_confidence": app_score.avg_confidence,
                "overall_tier": app_score.overall_tier,
                "sophistication_score": app_score.sophistication_score,
            },
            "distribution": {
                "protection_types": app_score.protection_types,
                "confidence_breakdown": app_score.confidence_distribution,
                "multi_layer_count": app_score.multi_layer_protections,
                "defense_breadth": app_score.defense_breadth,
                "defense_depth": app_score.defense_depth,
            },
            "method_stats": {
                "total_methods": len(method_scores),
                "protected_methods": len([m for m in method_scores if m.method_confidence > 0]),
                "avg_method_confidence": round(
                    sum(m.method_confidence for m in method_scores) / len(method_scores)
                    if method_scores else 0, 2
                ),
                "sophistication_distribution": self._sophistication_dist(method_scores),
            },
            "class_stats": {
                "total_classes": len(class_scores),
                "avg_class_confidence": round(
                    sum(c.class_confidence for c in class_scores) / len(class_scores)
                    if class_scores else 0, 2
                ),
                "avg_coverage": round(
                    sum(c.protection_coverage for c in class_scores) / len(class_scores)
                    if class_scores else 0, 2
                ),
            },
            "method_details": [asdict(m) for m in method_scores],
            "class_details": [asdict(c) for c in class_scores],
        }

    @staticmethod
    def _sophistication_dist(method_scores: List[MethodScore]) -> Dict[str, int]:
        """Count sophistication levels"""
        dist = {"simple": 0, "moderate": 0, "advanced": 0, "sophisticated": 0}
        for ms in method_scores:
            dist[ms.sophistication_level] = dist.get(ms.sophistication_level, 0) + 1
        return dist


class ComparisonGenerator:
    """
    Generate comparison tables for multiple apps.
    
    Used for paper figures showing ILEA vs other tools vs ground truth.
    """
    
    @staticmethod
    def compare_apps(app_scores: List[AppScore]) -> Dict:
        """
        Generate comparison matrix across apps.
        
        Returns:
            {
                "comparison_table": [...],
                "best_in_each_metric": {...},
                "overall_rankings": [...]
            }
        """
        if not app_scores:
            return {}
        
        # Build comparison table
        comparison_rows = []
        for score in app_scores:
            comparison_rows.append({
                "app_name": score.app_name,
                "total_findings": score.total_findings,
                "avg_confidence": score.avg_confidence,
                "max_confidence": score.max_confidence,
                "sophistication": score.sophistication_score,
                "breadth": score.defense_breadth,
                "depth": score.defense_depth,
                "overall_tier": score.overall_tier,
            })
        
        # Find best in each metric
        metrics = ["avg_confidence", "sophistication", "breadth", "depth"]
        best_in_metric = {}
        for metric in metrics:
            best_app = max(app_scores, key=lambda s: getattr(s, metric.split('_')[0]))
            best_in_metric[metric] = best_app.app_name
        
        # Overall ranking
        rankings = sorted(app_scores, 
                         key=lambda s: s.sophistication_score, 
                         reverse=True)
        ranked_names = [r.app_name for r in rankings]
        
        return {
            "comparison_table": comparison_rows,
            "best_in_each_metric": best_in_metric,
            "overall_rankings": ranked_names,
            "app_count": len(app_scores),
        }

    @staticmethod
    def generate_markdown_table(comparison_data: Dict) -> str:
        """
        Generate markdown table for paper inclusion.
        """
        rows = comparison_data.get("comparison_table", [])
        if not rows:
            return ""
        
        # Header
        md = "| App | Findings | Avg Conf | Sophist | Breadth | Depth | Tier |\n"
        md += "|-----|----------|----------|---------|---------|-------|------|\n"
        
        # Rows
        for row in rows:
            md += f"| {row['app_name']} | "
            md += f"{row['total_findings']} | "
            md += f"{row['avg_confidence']:.2f} | "
            md += f"{row['sophistication']:.2f} | "
            md += f"{row['breadth']} | "
            md += f"{row['depth']:.1f} | "
            md += f"{row['overall_tier']} |\n"
        
        return md
