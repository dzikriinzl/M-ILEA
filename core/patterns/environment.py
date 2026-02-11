import json
import logging
from core.patterns.base import BaseProtectionPattern
from core.analyzer.models import ProtectionCandidate

class RootDetectionPattern(BaseProtectionPattern):
    PATTERN_NAME = "Root / Emulator Detection"
    IMPACT_HINT = "Detects environment manipulation (Root/Emulator)"

    def __init__(self):
        try:
            with open("data/indicators.json") as f:
                self.indicators = json.load(f)
        except Exception as e:
            logging.error(f"Failed to load indicators: {e}")
            self.indicators = {"root_indicators": [], "emulator_indicators": [], "benign_extensions": []}

    def match(self, sink_hit, context=None):
        if sink_hit.sink.get("risk") not in ["Environment Verification", "Root Detection", "Emulator Detection"]:
            return None

        all_args = getattr(sink_hit, 'arguments', [])
        has_indicator = False
        
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
                location={
                    "class": sink_hit.class_name,
                    "method": sink_hit.method_name,
                    "line": sink_hit.line_number,
                    "layer": getattr(sink_hit, 'layer', 'Java')
                },
                evidence=f"Matched indicators in: {', '.join(all_args)}",
                impact_hint=self.IMPACT_HINT,
                confidence_signal=sink_hit
            )
        return None