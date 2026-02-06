class FindingGrouper:
    def group(self, findings):
        grouped = {}

        for f in findings:
            # REVISI: Mengubah tuple menjadi string unik menggunakan pemisah '|'
            # Ini mencegah error "tuple is not a valid JSON key"
            key = f"{f.protection_type}|{f.semantic_label}|{f.taxonomy['strategy']}"

            if key not in grouped:
                grouped[key] = {
                    "protection_type": f.protection_type,
                    "semantic_label": f.semantic_label,
                    "taxonomy": f.taxonomy,
                    "max_score": f.confidence_score,
                    "locations": []
                }

            # Menghindari duplikasi lokasi yang identik
            if f.location not in grouped[key]["locations"]:
                grouped[key]["locations"].append(f.location)

            # Update skor tertinggi jika ditemukan instance yang lebih meyakinkan
            grouped[key]["max_score"] = max(
                grouped[key]["max_score"],
                f.confidence_score
            )

        return grouped
