class BaseProtectionPattern:
    PATTERN_NAME = "Generic Protection"
    IMPACT_HINT = "Unknown"

    def match(self, sink_hit, context=None):
        """
        Setiap pola sekarang menerima context (untuk data framework/native).
        """
        raise NotImplementedError

    def is_false_positive(self, sink_hit) -> bool:
        """
        Override untuk menyaring penggunaan API yang bersifat benign (normal).
        """
        return False
