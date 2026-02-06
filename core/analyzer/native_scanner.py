import re

class NativeSinkScanner:
    def __init__(self, sink_registry):
        self.sink_registry = sink_registry

    def scan(self, disassembly_lines):
        hits = []
        for idx, line in enumerate(disassembly_lines):
            # A. Syscall Detection (svc #id)
            if "svc" in line:
                match = re.search(r"(?:#|svc\s+)(0x[0-9a-fA-F]+|[0-9]+)", line)
                if match:
                    val = match.group(1)
                    syscall_id = int(val, 16) if val.startswith("0x") else int(val)
                    sink = self.sink_registry.match_native_syscall(syscall_id)
                    if sink:
                        hits.append({"sink": sink, "line": idx, "evidence": line.strip(), "layer": "Native"})

            # B. Sensitive Symbol Detection (e.g., __system_property_get)
            for sink in self.sink_registry.get_native_symbols():
                if sink["name"] in line:
                    hits.append({"sink": sink, "line": idx, "evidence": line.strip(), "layer": "Native"})

        return hits