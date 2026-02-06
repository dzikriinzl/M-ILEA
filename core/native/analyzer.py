from core.native.symbol_scanner import NativeEvidenceScanner

class NativeAnalyzer:
    def __init__(self, sink_registry):
        self.sink_registry = sink_registry
        self.scanner = NativeEvidenceScanner(sink_registry)

    def analyze_files(self, so_files):
        native_hits = []
        for so_file in so_files:
            try:
                hits = self.scanner.scan(so_file)
                native_hits.extend(hits)
            except Exception:
                continue
        return native_hits
