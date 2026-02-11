"""
Multi-Level Confidence Scoring System v2.0

Architecture:
- Signal Level (0-1.0): Individual API call/pattern
- Method Level: Aggregate of signals in a method
- Class Level: Aggregate across methods in a class
- App Level: Overall security posture

Reference: ARAP paper on self-protection mechanism comparison
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ScoringTier(Enum):
    """Scoring hierarchy levels"""
    SIGNAL = "signal"          # Per-API/pattern detection
    METHOD = "method"          # Per-method aggregate
    CLASS = "class"            # Per-class aggregate
    APP = "app"                # Overall app confidence


@dataclass
class SignalFactors:
    """Components that contribute to signal-level confidence"""
    has_api_match: bool = False         # API call detected
    has_string_match: bool = False      # Sensitive string found
    has_conditional_logic: bool = False # Inside control flow
    is_native_layer: bool = False       # Native code layer
    has_multiple_checks: bool = False   # Redundant checks
    is_in_callback: bool = False        # Inside listener/callback
    context_strength: float = 0.0       # Context-based strength (0-1)


@dataclass
class MethodScore:
    """Aggregate score for a method"""
    method_name: str
    num_signals: int
    avg_signal_confidence: float
    max_signal_confidence: float
    method_confidence: float            # Final method score
    sophistication_level: str           # simple, moderate, advanced, sophisticated


@dataclass
class ClassScore:
    """Aggregate score for a class"""
    class_name: str
    num_methods: int
    num_protection_methods: int
    avg_method_confidence: float
    class_confidence: float
    protection_coverage: float          # % methods with protection
    sophistication_level: str


@dataclass
class AppScore:
    """Overall app security posture"""
    app_name: str
    total_findings: int
    avg_confidence: float
    max_confidence: float
    
    # Distribution
    protection_types: Dict[str, int]    # Count per type
    confidence_distribution: Dict[str, int]  # Count per confidence range
    
    # Sophistication metrics
    sophistication_score: float         # Overall sophistication
    multi_layer_protections: int        # Protection in multiple layers
    defense_breadth: int                # Number of different protection types
    defense_depth: int                  # Number of protections per method
    
    # Overall rating
    overall_tier: str                   # Low, Medium, High, Very High


class ConfidenceScorer:
    """
    Signal-level (per-line) confidence scorer.
    
    Scoring Formula:
    ================
    Base Score (API): 0.4
    + String Match (if present): 0.2
    + Conditional Logic (if inside IF/ELSE): 0.15
    + Native Layer (if in native code): 0.1
    + Context Strength (semantic analysis): 0.05
    + Redundancy Bonus (multiple checks): 0.1
    
    Total possible: 1.0
    
    Example:
    - API only: 0.4
    - API + String: 0.6
    - API + String + Logic: 0.75
    - API + all: 1.0
    """
    
    def __init__(self):
        # REVISED Weights (Total 1.0)
        self.weights = {
            "api": 0.40,                # API/sink match found
            "string": 0.20,             # Sensitive string match
            "logic": 0.15,              # Conditional control flow
            "native": 0.10,             # Native code layer
            "context": 0.05,            # Semantic context strength
            "redundancy": 0.10,         # Multiple checks
        }
        
        logger.info(f"ConfidenceScorer initialized with weights: {self.weights}")

    def _get_val(self, obj, key):
        """Safe value extraction from dict or dataclass"""
        if isinstance(obj, dict):
            return obj.get(key, False)
        val = getattr(obj, key, None)
        if val is None and hasattr(obj, 'sink'):
            val = obj.sink.get(key, False) if isinstance(obj.sink, dict) else getattr(obj.sink, key, False)
        return val

    def score_signal(self, signal) -> Tuple[float, SignalFactors]:
        """
        Calculate signal-level confidence.
        
        Returns:
            Tuple of (confidence_score, factor_breakdown)
        """
        factors = SignalFactors()
        score = 0.0
        
        # API Match (base)
        if self._get_val(signal, "has_api_match") or self._get_val(signal, "sink"):
            factors.has_api_match = True
            score += self.weights["api"]
        
        # String Match
        if self._get_val(signal, "has_string_match"):
            factors.has_string_match = True
            score += self.weights["string"]
        
        # Conditional Logic
        if self._get_val(signal, "conditional"):
            factors.has_conditional_logic = True
            score += self.weights["logic"]
        
        # Native Layer
        if self._get_val(signal, "layer") == "Native":
            factors.is_native_layer = True
            score += self.weights["native"]
        
        # Context Strength
        context_val = self._get_val(signal, "context_strength")
        if isinstance(context_val, (int, float)) and context_val > 0:
            factors.context_strength = min(context_val, 1.0)
            score += self.weights["context"] * factors.context_strength
        
        # Redundancy Bonus (multiple indicators)
        indicators_found = sum([
            factors.has_api_match,
            factors.has_string_match,
            factors.has_conditional_logic,
            factors.is_native_layer
        ])
        if indicators_found >= 3:  # 3+ factors detected
            factors.has_multiple_checks = True
            score += self.weights["redundancy"]
        
        # Cap at 1.0
        final_score = round(min(score, 1.0), 2)
        
        return final_score, factors

    def breakdown(self, signal) -> Dict:
        """Generate detailed breakdown of scoring factors"""
        score, factors = self.score_signal(signal)
        
        return {
            "confidence_score": score,
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


class MethodLevelScorer:
    """
    Aggregate confidence at method level.
    
    Logic:
    - Collect all signals within a method
    - Calculate: avg + max + distribution
    - Apply sophistication multiplier
    - Consider redundancy (how many different protection methods)
    """
    
    @staticmethod
    def score_method(method_name: str, signals: List) -> MethodScore:
        """
        Score a single method based on its signals.
        
        Args:
            method_name: Name of the method
            signals: List of signal objects with confidence scores
            
        Returns:
            MethodScore with aggregated metrics
        """
        if not signals:
            return MethodScore(
                method_name=method_name,
                num_signals=0,
                avg_signal_confidence=0.0,
                max_signal_confidence=0.0,
                method_confidence=0.0,
                sophistication_level="none"
            )
        
        scorer = ConfidenceScorer()
        confidences = [scorer.score_signal(s)[0] for s in signals]
        
        num_signals = len(signals)
        avg_confidence = sum(confidences) / num_signals
        max_confidence = max(confidences)
        
        # Sophistication Analysis
        if num_signals == 1:
            sophistication = "simple"
        elif num_signals <= 3 and max_confidence >= 0.7:
            sophistication = "moderate"
        elif num_signals <= 5 and max_confidence >= 0.8:
            sophistication = "advanced"
        else:
            sophistication = "sophisticated"
        
        # Method-level confidence calculation
        # Formula: (avg * 0.4) + (max * 0.3) + (sophistication_bonus * 0.3)
        sophistication_bonus = {
            "simple": 0.2,
            "moderate": 0.5,
            "advanced": 0.75,
            "sophisticated": 1.0
        }[sophistication]
        
        method_confidence = round(
            (avg_confidence * 0.4) + (max_confidence * 0.3) + (sophistication_bonus * 0.3),
            2
        )
        
        return MethodScore(
            method_name=method_name,
            num_signals=num_signals,
            avg_signal_confidence=round(avg_confidence, 2),
            max_signal_confidence=max_confidence,
            method_confidence=method_confidence,
            sophistication_level=sophistication
        )


class ClassLevelScorer:
    """
    Aggregate confidence at class level.
    
    Considers:
    - Number of protection methods
    - Distribution of confidence scores
    - Coverage percentage
    - Overall class sophistication
    """
    
    @staticmethod
    def score_class(class_name: str, method_scores: List[MethodScore]) -> ClassScore:
        """
        Score a class based on its methods.
        
        Args:
            class_name: Name of the class
            method_scores: List of MethodScore objects
            
        Returns:
            ClassScore with aggregated metrics
        """
        if not method_scores:
            return ClassScore(
                class_name=class_name,
                num_methods=0,
                num_protection_methods=0,
                avg_method_confidence=0.0,
                class_confidence=0.0,
                protection_coverage=0.0,
                sophistication_level="none"
            )
        
        # Filter methods with actual protection
        protection_methods = [m for m in method_scores if m.method_confidence > 0]
        
        confidences = [m.method_confidence for m in protection_methods]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Coverage: percentage of methods with protection
        total_methods = len(method_scores)
        coverage = (len(protection_methods) / total_methods) if total_methods > 0 else 0
        
        # Sophistication: based on distribution and depth
        sophistication_levels = [m.sophistication_level for m in protection_methods]
        avg_sophistication = sum(
            {"simple": 1, "moderate": 2, "advanced": 3, "sophisticated": 4}.get(s, 0)
            for s in sophistication_levels
        ) / len(sophistication_levels) if sophistication_levels else 0
        
        if avg_sophistication >= 3:
            sophistication = "sophisticated"
        elif avg_sophistication >= 2.5:
            sophistication = "advanced"
        elif avg_sophistication >= 1.5:
            sophistication = "moderate"
        else:
            sophistication = "simple"
        
        # Class-level confidence
        # Formula: (avg_method_conf * 0.5) + (coverage * 0.3) + (sophistication_bonus * 0.2)
        sophistication_bonus = {
            "simple": 0.2,
            "moderate": 0.5,
            "advanced": 0.8,
            "sophisticated": 1.0
        }[sophistication]
        
        class_confidence = round(
            (avg_confidence * 0.5) + (coverage * 0.3) + (sophistication_bonus * 0.2),
            2
        )
        
        return ClassScore(
            class_name=class_name,
            num_methods=total_methods,
            num_protection_methods=len(protection_methods),
            avg_method_confidence=round(avg_confidence, 2),
            class_confidence=class_confidence,
            protection_coverage=round(coverage, 2),
            sophistication_level=sophistication
        )


class AppLevelScorer:
    """
    Aggregate confidence at application level.
    
    Considers:
    - Overall protection distribution
    - Multi-layer protections
    - Breadth and depth of protections
    - Sophistication across app
    """
    
    @staticmethod
    def score_app(app_name: str, findings: List) -> AppScore:
        """
        Score entire application.
        
        Args:
            app_name: Name of the application
            findings: List of finding objects with confidence scores
            
        Returns:
            AppScore with overall metrics
        """
        if not findings:
            return AppScore(
                app_name=app_name,
                total_findings=0,
                avg_confidence=0.0,
                max_confidence=0.0,
                protection_types={},
                confidence_distribution={},
                sophistication_score=0.0,
                multi_layer_protections=0,
                defense_breadth=0,
                defense_depth=0,
                overall_tier="Low"
            )
        
        # Basic metrics
        total_findings = len(findings)
        confidences = [
            getattr(f, 'confidence_score', getattr(f, 'signal_confidence', 0.4))
            for f in findings
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        max_confidence = max(confidences) if confidences else 0
        
        # Protection type distribution
        protection_types = {}
        for f in findings:
            ptype = getattr(f, 'protection_type', 'Unknown')
            protection_types[ptype] = protection_types.get(ptype, 0) + 1
        
        # Confidence distribution (bucket into ranges)
        confidence_distribution = {
            "high": 0,      # 0.8+
            "medium": 0,    # 0.6-0.8
            "low": 0        # <0.6
        }
        for conf in confidences:
            if conf >= 0.8:
                confidence_distribution["high"] += 1
            elif conf >= 0.6:
                confidence_distribution["medium"] += 1
            else:
                confidence_distribution["low"] += 1
        
        # Multi-layer detection
        # Check if protections span multiple file types/locations
        locations = set()
        for f in findings:
            loc = getattr(f, 'location', {})
            if isinstance(loc, dict):
                locations.add(loc.get('class', 'Unknown'))
        multi_layer = len(locations)
        
        # Defense breadth (number of different protection types)
        defense_breadth = len(protection_types)
        
        # Defense depth (avg protections per class)
        defense_depth = total_findings / multi_layer if multi_layer > 0 else 0
        
        # Sophistication score
        # Formula: (avg_confidence * 0.4) + (breadth_factor * 0.3) + (depth_factor * 0.3)
        breadth_factor = min(defense_breadth / 5, 1.0)  # Max 5 types
        depth_factor = min(defense_depth / 3, 1.0)      # Max 3 per class
        
        sophistication_score = round(
            (avg_confidence * 0.4) + (breadth_factor * 0.3) + (depth_factor * 0.3),
            2
        )
        
        # Overall tier determination
        if sophistication_score >= 0.8:
            overall_tier = "Very High"
        elif sophistication_score >= 0.6:
            overall_tier = "High"
        elif sophistication_score >= 0.4:
            overall_tier = "Medium"
        else:
            overall_tier = "Low"
        
        return AppScore(
            app_name=app_name,
            total_findings=total_findings,
            avg_confidence=round(avg_confidence, 2),
            max_confidence=max_confidence,
            protection_types=protection_types,
            confidence_distribution=confidence_distribution,
            sophistication_score=sophistication_score,
            multi_layer_protections=multi_layer,
            defense_breadth=defense_breadth,
            defense_depth=round(defense_depth, 2),
            overall_tier=overall_tier
        )
