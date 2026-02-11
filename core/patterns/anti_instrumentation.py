from core.patterns.base import BaseProtectionPattern
from core.analyzer.models import ProtectionCandidate

class AntiDebugPattern(BaseProtectionPattern):
    PATTERN_NAME = "Anti-Debugging"
    IMPACT_HINT = "Blocks dynamic instrumentation / Debugging"

    def match(self, sink_hit, context=None):
        # Sesuaikan dengan risk di sink_catalog.json
        if sink_hit.sink.get("risk") in ["Anti-Debugging", "Anti-Debugging Logic"]:
            return ProtectionCandidate(
                pattern_type=self.PATTERN_NAME,
                location={
                    "class": sink_hit.class_name,
                    "method": sink_hit.method_name,
                    "line": sink_hit.line_number,
                    "layer": getattr(sink_hit, 'layer', 'Java')
                },
                evidence=f"Debugger detection check: {sink_hit.sink.get('name')}",
                impact_hint=self.IMPACT_HINT,
                confidence_signal=sink_hit
            )
        return None