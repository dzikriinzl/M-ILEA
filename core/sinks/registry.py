import json
import re
import logging
from typing import List, Dict, Optional


class SinkRegistry:
    """
    Context-Aware Security-Sensitive Sink Registry
    M-ILEA Knowledge Base (Step 1)
    """

    def __init__(self, catalog_path: str):
        # 1. Load Main Catalog (sinks)
        try:
            with open(catalog_path, "r") as f:
                self.catalog = json.load(f)
        except Exception as e:
            logging.error(f"Failed to load sink catalog: {e}")
            self.catalog = {}

        self._flattened_sinks = self._flatten_catalog()

        # 2. Load Indicators (root/emulator/benign strings)
        # Menghubungkan Step 1 dengan data indikator mentah
        self.indicators = self._load_indicators("data/indicators.json")

    def _load_indicators(self, path: str) -> Dict:
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            logging.warning("indicators.json not found, string-based detection will be limited.")
            return {"root_indicators": [], "emulator_indicators": []}

    def _flatten_catalog(self) -> List[Dict]:
        sinks = []
        for category in self.catalog.values():
            if isinstance(category, dict):
                for sink in category.get("sinks", []):
                    sinks.append(sink)
        return sinks

    def get_all_sinks(self) -> List[Dict]:
        return self._flattened_sinks

    def match_sink(self, api_call: str) -> Optional[Dict]:
        """
        Match an API call or native symbol to a registered sink.
        Sinergi dengan Step 2a (Java Scanner).
        """
        for sink in self._flattened_sinks:
            match_type = sink.get("match_type", "fqn")
            target_name = sink["name"]

            # Flexible FQN Matching (Smali aware)
            if match_type == "fqn":
                # Mencocokkan 'java.io.File.exists' dengan 'File.exists' 
                # atau format Smali 'Ljava/io/File;->exists'
                if target_name in api_call or api_call in target_name:
                    return sink

            elif match_type == "regex":
                if re.search(target_name, api_call):
                    return sink

            elif match_type == "native":
                if api_call == target_name:
                    return sink

            elif match_type == "path":
                if target_name in api_call:
                    return sink

        return None

    def match_string_indicator(self, string_val: str) -> Optional[Dict]:
        """
        Mencocokkan string mentah (const-string) dengan indikator ancaman.
        Menyelesaikan error 'no attribute match_string_indicator'.
        """
        # Cek indikator Root (e.g., /system/xbin/su)
        for indicator in self.indicators.get("root_indicators", []):
            if indicator in string_val:
                return {
                    "name": string_val,
                    "layer": "Java",
                    "risk": "Root Detection",
                    "confidence": 0.8,
                    "type": "string_match"
                }
        
        # Cek indikator Emulator
        for indicator in self.indicators.get("emulator_indicators", []):
            if indicator in string_val:
                return {
                    "name": string_val,
                    "layer": "Java",
                    "risk": "Emulator Detection",
                    "confidence": 0.8,
                    "type": "string_match"
                }
        return None

    def is_security_relevant_call(self, sink: Dict, call_args: List[str]) -> bool:
        """
        Contextual validation untuk sink yang bersifat dual-use.
        """
        if not sink: return False
        if not sink.get("dual_use", False): return True

        context_hint = sink.get("context_hint", {})
        suspicious_args = context_hint.get("suspicious_args", [])

        # Jika salah satu argumen (e.g. path file) ada di list mencurigakan
        for arg in call_args:
            if any(susp in arg for susp in suspicious_args):
                return True
        return False

    def match_native_syscall(self, syscall_id: int) -> Optional[Dict]:
        for sink in self._flattened_sinks:
            if sink.get("syscall_id") == syscall_id:
                return sink
        return None

    def get_native_symbols(self) -> List[Dict]:
        """Digunakan oleh Native Scanner"""
        return [s for s in self._flattened_sinks if s.get("layer") == "Native"]
