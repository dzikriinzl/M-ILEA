from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class LocalizedProtection:
    pattern_type: str
    impact_hint: str

    location: Dict          # class, method, full_signature, line, native_offset, layer
    evidence: Dict

    confidence_score: float
    confidence_breakdown: Dict

    def get_taxonomy_tuple(self):
        """
        Prepare 4D taxonomy mapping (used in Step 6)
        """
        return {
            "purpose": self.pattern_type,
            "layer": self.location.get("layer"),
            "strategy": (
                "Memory-based"
                if "maps" in str(self.evidence)
                else "API-based"
            ),
            "impact": self.impact_hint
        }
