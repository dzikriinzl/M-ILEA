from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class NativeSinkHit:
    sink: Dict
    library: str
    offset: str
    evidence: str

    # Context Flags
    is_syscall: bool
    is_symbol: bool
    is_string_based: bool
    
    # Sinkronisasi dengan Java models (Wajib untuk Step 3-6)
    class_name: str = "NativeCode" 
    method_name: str = "BinaryInstruction"
    line_number: int = 0
    arguments: List[str] = field(default_factory=list)
    conditional: bool = False
    context_snippet: Optional[List[str]] = None
    layer: str = "Native" # Label pembeda untuk Slicer