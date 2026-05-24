from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdvisoryEvidence:
    evidence_type: str
    status: str = "not_configured"
    authority: str = "advisory_only"
    claim_boundary: str = "cannot_confirm_fall_or_injury"

    def to_dict(self) -> dict[str, str]:
        return {
            "evidence_type": self.evidence_type,
            "status": self.status,
            "authority": self.authority,
            "claim_boundary": self.claim_boundary,
        }


def default_advisory_evidence() -> list[dict[str, str]]:
    return [
        AdvisoryEvidence("pose").to_dict(),
        AdvisoryEvidence("depth").to_dict(),
        AdvisoryEvidence("segmentation").to_dict(),
    ]
