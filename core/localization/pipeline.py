from core.localization.engine import LocalizationEngine
from core.scoring.scorer import ConfidenceScorer
from core.localization.models import LocalizedProtection

class LocalizationPipeline:
    def __init__(self):
        # Inisialisasi Scorer terlebih dahulu
        self.scorer = ConfidenceScorer()
        # Masukkan scorer ke dalam engine (Dependency Injection)
        self.localizer = LocalizationEngine(scorer=self.scorer)

    def process(self, candidates):
        """
        Mengonversi ProtectionCandidate menjadi LocalizedProtection 
        dengan data lokasi dan skor yang lengkap.
        """
        # Gunakan method process dari engine yang sudah kita perbaiki
        processed_candidates = self.localizer.process(candidates)
        
        results = []
        for c in processed_candidates:
            # Bungkus ke dalam model LocalizedProtection untuk Step 5 & 6
            results.append(
                LocalizedProtection(
                    pattern_type=c.pattern_type,
                    impact_hint=c.impact_hint,
                    location=c.location,
                    evidence=c.evidence,
                    confidence_score=getattr(c, 'confidence_score', 0.0),
                    confidence_breakdown=getattr(c, 'score_breakdown', {})
                )
            )
        return results