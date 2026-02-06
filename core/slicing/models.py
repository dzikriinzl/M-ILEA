from dataclasses import dataclass
from typing import List, Dict


@dataclass
class EvidenceSlice:
    pattern_type: str
    impact_hint: str

    location: Dict
    code_snippet: List[str]

    highlighted_lines: List[int]   # index baris sink
    semantic_label: str
    confidence_score: float
