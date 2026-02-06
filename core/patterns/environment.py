import json
import logging
from core.patterns.base import BaseProtectionPattern
from core.patterns.models import ProtectionCandidate, ConfidenceSignal

class RootDetectionPattern(BaseProtectionPattern):
    PATTERN_NAME = "Root / Emulator Detection"
    IMPACT_HINT = "Detects environment manipulation (Root/Emulator)"

    def __init__(self):
        try:
            with open("data/indicators.json") as f:
                self.indicators = json.load(f)
        except Exception as e:
            logging.error(f"Failed to load indicators in RootDetectionPattern: {e}")
            self.indicators = {"root_indicators": [], "benign_extensions": []}

    def is_false_positive(self, sink_hit) -> bool:
        # Cek apakah argumen API berakhir dengan ekstensi benign (seperti .jpg)
        for arg in getattr(sink_hit, 'arguments', []):
            for ext in self.indicators.get("benign_extensions", []):
                if arg.lower().endswith(ext.lower()):
                    return True
        return False

    def match(self, sink_hit, context=None):
        # Validasi kategori risiko
        if sink_hit.sink.get("risk") not in ["Environment Verification", "Root Detection", "Emulator Detection"]:
            return None

        # Filter false positive
        if self.is_false_positive(sink_hit):
            return None

        # Logic Deteksi: Cek argumen API atau nilai string
        has_indicator = False
        all_args = getattr(sink_hit, 'arguments', [])
        
        for arg in all_args:
            if any(ind in arg for ind in self.indicators.get("root_indicators", [])):
                has_indicator = True
                break
            if any(ind in arg for ind in self.indicators.get("emulator_indicators", [])):
                has_indicator = True
                break

        if has_indicator:
            return ProtectionCandidate(
                pattern_type=self.PATTERN_NAME,
                sink=sink_hit.sink,
                class_name=sink_hit.class_name,
                method_name=sink_hit.method_name,
                line_number=sink_hit.line_number,
                evidence={
                    "arguments": all_args,
                    "conditional": getattr(sink_hit, 'conditional', False),
                    "snippet": getattr(sink_hit, 'context_snippet', [])
                },
                impact_hint=self.IMPACT_HINT,
                confidence_signal=ConfidenceSignal(
                    has_string_match=True,
                    has_api_match=True,
                    has_control_flow_logic=getattr(sink_hit, 'conditional', False),
                    is_native_implementation=sink_hit.sink.get("layer") == "Native"
                )
            )
        return None
