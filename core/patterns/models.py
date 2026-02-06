from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ConfidenceSignal:
    has_string_match: bool
    has_api_match: bool
    has_control_flow_logic: bool
    is_native_implementation: bool


@dataclass
class ProtectionCandidate:
    pattern_type: str
    sink: Dict

    class_name: str
    method_name: str
    line_number: int

    evidence: Dict
    impact_hint: str

    confidence_signal: ConfidenceSignal
