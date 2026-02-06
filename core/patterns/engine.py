from core.patterns.environment import RootDetectionPattern
from core.patterns.anti_instrumentation import AntiDebugPattern
from core.patterns.communication import SSLPinningPattern

class ProtectionPatternEngine:
    def __init__(self, context=None):
        # Simpan context (misal: {'frameworks': ['Flutter']})
        self.context = context
        # ORDER MATTERS: most specific → generic
        self.patterns = [
            SSLPinningPattern(),
            AntiDebugPattern(),
            RootDetectionPattern()
        ]

    def analyze(self, sink_hits):
        candidates = []

        for hit in sink_hits:
            for pattern in self.patterns:
                # Kirim self.context ke setiap modul pattern
                result = pattern.match(hit, context=self.context)
                if result:
                    candidates.append(result)
                    break
        return candidates
