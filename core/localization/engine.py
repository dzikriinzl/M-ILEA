
class LocalizationEngine:
    def localize(self, candidate):
        location = {
            "class": candidate.class_name,
            "method": candidate.method_name,
            "full_signature": f"{candidate.class_name}->{candidate.method_name}",
            "line": candidate.line_number,
            "layer": candidate.sink.get("layer", "Unknown")
        }

        # Native localization (RVA / symbol-aware)
        if candidate.sink.get("layer") == "Native":
            location["native_offset"] = candidate.evidence.get(
                "native_offset", "Unknown"
            )

        return location

