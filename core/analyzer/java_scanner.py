import re
from typing import List
from core.analyzer.models import SinkHit

class JavaSinkScanner:
    def __init__(self, sink_registry):
        self.sink_registry = sink_registry

    def scan_method(self, class_name: str, method_name: str, code_lines: List[str]) -> List[SinkHit]:
        hits = []
        is_obfuscated = len(method_name) <= 2

        for idx, line in enumerate(code_lines):
            # A. Deteksi API Call (invoke-*)
            if "invoke-" in line:
                api_call, registers = self._extract_invoke(line)
                sink = self.sink_registry.match_sink(api_call)

                if sink:
                    args = self._resolve_arguments(code_lines, idx, registers)
                    snippet = code_lines[max(0, idx - 2): idx + 3]

                    hits.append(SinkHit(
                        sink=sink,
                        class_name=class_name,
                        method_name=method_name,
                        line_number=idx + 1,
                        arguments=args,
                        conditional=self._is_conditional_context(code_lines, idx),
                        is_obfuscated=is_obfuscated,
                        context_snippet=snippet
                    ))
            
            # B. Deteksi String-Based Evidence (Penting untuk Root Detection AndroGoat)
            elif "const-string" in line:
                string_val = line.split(",")[-1].strip().strip('"')
                # Cek apakah string ini mencurigakan (su, magisk, dll)
                sink = self.sink_registry.match_string_indicator(string_val)
                if sink:
                    hits.append(SinkHit(
                        sink=sink,
                        class_name=class_name,
                        method_name=method_name,
                        line_number=idx + 1,
                        arguments=[string_val],
                        conditional=self._is_conditional_context(code_lines, idx),
                        is_obfuscated=is_obfuscated,
                        context_snippet=[line.strip()]
                    ))

        return hits

    def _extract_invoke(self, line: str):
        # Ekstrak Registers
        reg_match = re.search(r"\{([^\}]+)\}", line)
        registers = [r.strip() for r in reg_match.group(1).split(",")] if reg_match else []

        # Ekstrak FQN (Ljava/io/File;->exists menjadi java.io.File.exists)
        match = re.search(r"(L[^;]+;)->([^\(]+)", line)
        if match:
            class_part = match.group(1).lstrip("L").rstrip(";").replace("/", ".")
            method_part = match.group(2)
            api_call = f"{class_part}.{method_part}"
        else:
            api_call = ""
        return api_call, registers

    def _resolve_arguments(self, code_lines: List[str], idx: int, registers: List[str]) -> List[str]:
        args = []
        scan_limit = 15
        for i in range(idx - 1, max(-1, idx - scan_limit), -1):
            line = code_lines[i]
            for reg in registers:
                if f"const-string {reg}," in line:
                    arg = line.split(",")[-1].strip().strip('"')
                    args.append(arg)
        return args

    def _is_conditional_context(self, code_lines: List[str], idx: int) -> bool:
        # Cek apakah ada kontrol alur (if-eq, if-nez, dll) di dekat sink
        scan_range = 3
        for i in range(max(0, idx - scan_range), min(len(code_lines), idx + scan_range)):
            if "if-" in code_lines[i]:
                return True
        return False
