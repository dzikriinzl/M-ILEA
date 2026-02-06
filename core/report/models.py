from dataclasses import dataclass
from typing import Dict, List


@dataclass
class FinalFinding:
    protection_type: str
    taxonomy: Dict

    location: Dict
    semantic_label: str

    confidence_score: float
    evidence_snippet: List[str]


@dataclass
class GroupedFinding:
    protection_type: str
    taxonomy: Dict
    semantic_label: str

    locations: List[Dict]              # multiple class/method/offset
    max_confidence_score: float
    representative_evidence: List[str]
