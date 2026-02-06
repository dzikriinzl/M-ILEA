import os
from core.native.models import NativeSinkHit

class NativeEvidenceScanner:
    NATIVE_STRING_INDICATORS = {
        b"/proc/self/maps": "Memory-based Anti-Instrumentation",
        b"SSL_set_custom_verify": "BoringSSL / Flutter SSL Pinning",
        b"frida": "Frida Instrumentation Detection",
        b"ptrace": "Anti-Debugging Logic",
        b"TracerPid": "Debugger Status Check",
        b"/system/bin/su": "Native Root Verification"
    }

    def __init__(self, sink_registry):
        self.sink_registry = sink_registry

    def scan(self, so_path):
        hits = []
        if not os.path.exists(so_path):
            return hits

        with open(so_path, "rb") as f:
            binary_data = f.read()

        # 1. SCAN BERDASARKAN SINK REGISTRY
        native_sinks = self.sink_registry.get_sinks_by_layer("Native")
        for sink in native_sinks:
            symbol_name = sink.get("name").encode()
            offset = binary_data.find(symbol_name)
            if offset != -1:
                hits.append(self._create_hit(sink, so_path, offset, symbol_name, is_symbol=True))

        # 2. STRING-BASED FALLBACK
        for indicator, description in self.NATIVE_STRING_INDICATORS.items():
            offset = binary_data.find(indicator)
            if offset != -1:
                if not any(h.offset == hex(offset) for h in hits):
                    mock_sink = {
                        "name": indicator.decode(errors="ignore"),
                        "risk": description,
                        "layer": "Native",
                        "confidence": 0.6 # Skor dasar untuk string match
                    }
                    hits.append(self._create_hit(mock_sink, so_path, offset, indicator, is_symbol=False))
        return hits

    def _create_hit(self, sink, so_path, offset, evidence, is_symbol):
        lib_name = os.path.basename(so_path)
        evidence_str = evidence.decode(errors="ignore")
        
        return NativeSinkHit(
            sink=sink,
            library=lib_name,
            offset=hex(offset),
            evidence=evidence_str,
            is_syscall=False,
            is_symbol=is_symbol,
            is_string_based=not is_symbol,
            # Menambahkan konteks untuk Pattern Engine
            arguments=[lib_name, evidence_str],
            context_snippet=[f"Binary Offset {hex(offset)}: {evidence_str}"],
            conditional=True # Native security checks hampir selalu conditional
        )