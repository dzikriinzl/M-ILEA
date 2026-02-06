import logging
from core.analyzer.java_scanner import JavaSinkScanner

class StaticAnalyzer:
    def __init__(self, sink_registry, decompiled_classes):
        self.sink_registry = sink_registry
        self.decompiled_classes = decompiled_classes
        self.scanner = JavaSinkScanner(sink_registry)

    def analyze(self):
        all_hits = []
        logging.info(f"Scanning {len(self.decompiled_classes)} classes for security sinks...")

        for cls in self.decompiled_classes:
            for method in cls.methods:
                hits = self.scanner.scan_method(
                    cls.name,
                    method.name,
                    method.code_lines
                )
                all_hits.extend(hits)
        
        return all_hits