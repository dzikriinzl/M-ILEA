from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class SinkHit:
    sink: Dict
    class_name: str
    method_name: str
    line_number: int
    arguments: List[str]
    conditional: bool
    caller: Optional[str] = None
    is_obfuscated: bool = False
    context_snippet: List[str] = field(default_factory=list)
    layer: str = "Java"

@dataclass
class ProtectionCandidate:
    pattern_type: str
    location: Dict[str, Any]
    evidence: str
    impact_hint: str
    confidence_signal: Any  # Objek SinkHit yang akan dikirim ke Scorer
    confidence_level: Optional[float] = None  # Explicit confidence from audit patterns
