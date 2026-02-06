from core.localization.engine import LocalizationEngine
from core.scoring.scorer import ConfidenceScorer
from core.localization.models import LocalizedProtection


class LocalizationPipeline:
    def __init__(self):
        self.localizer = LocalizationEngine()
        self.scorer = ConfidenceScorer()

    def process(self, candidates):
        results = []

        for c in candidates:
            location = self.localizer.localize(c)
            score = self.scorer.score(c.confidence_signal)
            breakdown = self.scorer.breakdown(c.confidence_signal)

            results.append(
                LocalizedProtection(
                    pattern_type=c.pattern_type,
                    impact_hint=c.impact_hint,
                    location=location,
                    evidence=c.evidence,
                    confidence_score=score,
                    confidence_breakdown=breakdown
                )
            )
        return results
