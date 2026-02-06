class ConfidenceScorer:
    def __init__(self):
        self.weights = {
            "api": 0.4,
            "string": 0.3,
            "control_flow": 0.2,
            "native": 0.1
        }

    def score(self, signal):
        total_score = 0.0
        if getattr(signal, "has_api_match", False): total_score += self.weights["api"]
        if getattr(signal, "has_string_match", False): total_score += self.weights["string"]
        if getattr(signal, "has_control_flow_logic", False): total_score += self.weights["control_flow"]
        if getattr(signal, "is_native_implementation", False): total_score += self.weights["native"]
        
        return round(min(total_score, 1.0), 2)