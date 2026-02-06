from core.report.models import FinalFinding
from core.report.taxonomy import TaxonomyMapper


class ReportBuilder:
    def __init__(self):
        self.taxonomy_mapper = TaxonomyMapper()

    def build(self, evidence_slices):
        report = []

        for e in evidence_slices:
            taxonomy = self.taxonomy_mapper.map(e)

            report.append(
                FinalFinding(
                    protection_type=e.pattern_type,
                    taxonomy=taxonomy,
                    location=e.location,
                    semantic_label=e.semantic_label,
                    confidence_score=e.confidence_score,
                    evidence_snippet=e.code_snippet
                )
            )
        return report

    def export_to_latex_table(self, grouped_findings):
        rows = []

        for key, data in grouped_findings.items():
            f = data["prototype"]
            rows.append(
                f"{f.protection_type} & "
                f"{f.taxonomy['layer']} & "
                f"{f.taxonomy['strategy']} & "
                f"{f.taxonomy['impact']} & "
                f"{data['max_score']:.2f} \\\\ \\hline"
            )

        return "\n".join(rows)
