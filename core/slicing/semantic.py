class SemanticLabeler:
    def label(self, pattern_type, evidence, location):
        # Pemetaan deskripsi mendalam ala Paper ARAP
        mapping = {
            "Root / Emulator Detection": [
                "Environment Integrity Check: Searching for privileged binaries (su, magisk)",
                "Infrastructure Validation: Inspecting system build tags and qemu props"
            ],
            "SSL Pinning": [
                "Network Trust Anchor: Enforcing custom X.509 certificate validation",
                "Communication Guard: Hardcoded public key pinning via OkHttp/TrustManager"
            ],
            "Anti-Debugging": [
                "Runtime Shield: Detecting ptrace attachment or JDWP state",
                "Analysis Prevention: Monitoring Debug.isDebuggerConnected() flags"
            ]
        }

        labels = mapping.get(pattern_type, ["Security-Relevant Logic Extraction"])
        
        # Logika pemilihan label berdasarkan konten evidence (misal: jika ada kata 'su')
        if "su" in str(evidence).lower() and pattern_type == "Root / Emulator Detection":
            return labels[0]
        
        return labels[-1]