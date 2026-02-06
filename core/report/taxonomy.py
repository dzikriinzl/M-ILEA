class TaxonomyMapper:
    def map(self, evidence_slice):
        return {
            "purpose": evidence_slice.pattern_type,
            "layer": evidence_slice.location.get("layer"),
            "strategy": self._infer_strategy(evidence_slice),
            "impact": evidence_slice.impact_hint
        }

    def _infer_strategy(self, evidence_slice):
        sink = evidence_slice.location.get("sink_metadata", {})
        code = " ".join(evidence_slice.code_snippet)

        # Sink-driven (robust)
        if sink.get("name") == "ptrace":
            return "Syscall / API-based"

        # Evidence-driven (fallback)
        if "/proc/self/maps" in code:
            return "Memory-based"
        if "/system" in code:
            return "File / Path-based"
        if "CertificatePinner" in code or "SSLContext" in code:
            return "API-based"
        if "checksum" in code:
            return "Checksum-based"

        return "Control-flow-based"
