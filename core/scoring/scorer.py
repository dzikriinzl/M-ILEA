class ConfidenceScorer:
    def __init__(self):
        # Bobot standar Akademik (Total 1.0)
        self.weights = {
            "api": 0.4,      # Pemicu API ditemukan
            "string": 0.3,   # Keyword sensitif ditemukan (e.g., "su")
            "logic": 0.2,    # Di dalam blok IF/ELSE
            "native": 0.1    # Lapisan Native (Lebih sulit di-bypass)
        }

    def _get_val(self, obj, key):
        if isinstance(obj, dict): return obj.get(key, False)
        # Cek atribut langsung atau di dalam dictionary 'sink'
        val = getattr(obj, key, None)
        if val is None and hasattr(obj, 'sink'):
            val = obj.sink.get(key, False)
        return val

    def score(self, signal):
        """
        Score calculation with support for audit pattern confidence levels.
        If a confidence_level is provided by audit patterns, use it as base score.
        """
        # Check if signal has explicit confidence level from audit patterns
        explicit_confidence = getattr(signal, 'confidence_level', None)
        if explicit_confidence is not None:
            # Use the confidence level from audit pattern as base
            return round(explicit_confidence, 2)
        
        # Fallback to traditional scoring for legacy patterns
        s = self.weights["api"]  # Base score
        
        if self._get_val(signal, "has_string_match"):
            s += self.weights["string"]
            
        if self._get_val(signal, "conditional"):
            s += self.weights["logic"]
            
        if self._get_val(signal, "layer") == "Native":
            s += self.weights["native"]
            
        return round(min(s, 1.0), 2)

    def breakdown(self, signal):
        """
        Provide breakdown of confidence scoring factors.
        """
        explicit_confidence = getattr(signal, 'confidence_level', None)
        
        return {
            "api_match": True,
            "string_indicator": bool(self._get_val(signal, "has_string_match")),
            "control_flow": bool(self._get_val(signal, "conditional")),
            "native_layer": self._get_val(signal, "layer") == "Native",
            "explicit_audit_confidence": explicit_confidence
        }
