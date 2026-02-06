from core.patterns.base import BaseProtectionPattern
from core.patterns.models import ProtectionCandidate

class AntiDebugPattern(BaseProtectionPattern):
    PATTERN_NAME = "Anti-Debugging"
    IMPACT_HINT = "Blocks dynamic instrumentation"

    def match(self, sink_hit, context=None):
        # Memastikan hit ini relevan dengan risiko Anti-Debugging
        if sink_hit.sink.get("risk") == "Anti-Debugging":
            return ProtectionCandidate(
                pattern_type=self.PATTERN_NAME,
                sink=sink_hit.sink,
                class_name=sink_hit.class_name,
                method_name=sink_hit.method_name,
                line_number=sink_hit.line_number,
                evidence={
                    "native": sink_hit.sink.get("layer") == "Native",
                    "conditional": getattr(sink_hit, 'conditional', False),
                    "snippet": getattr(sink_hit, 'context_snippet', [])
                },
                impact_hint=self.IMPACT_HINT,
                confidence_hint={
                    "string": 0,
                    "api": 1,
                    "control_flow": 1 if getattr(sink_hit, 'conditional', False) else 0
                }
            )
        return None
