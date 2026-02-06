from dataclasses import dataclass
from typing import List, Optional, Dict

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
    context_snippet: List[str] = None
    layer: str = "Java" # Untuk membedakan Java/Native di Pattern Engine
