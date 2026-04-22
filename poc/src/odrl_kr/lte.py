"""Deterministic Legal Trigger Engine background for the S1 manuscript scenario."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


S1_PROVISIONS = [
    "kr:PIPA-28-2",
    "kr:PIPA-28-4",
    "kr:PIPA-28-5",
    "kr:PIPA-28-7",
]


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def derive_candidate_provisions(asset: dict[str, Any]) -> list[str]:
    """Derive candidate Korean legal provisions for implemented proof scenarios."""
    if (
        asset.get("scenario") == "S1"
        and asset.get("pseudonymized") is True
        and asset.get("purpose") == "research"
        and asset.get("transactionType") == "SPE"
    ):
        return list(S1_PROVISIONS)
    raise ValueError("Only the S1 pseudonymized viewing-log research scenario is implemented.")


def build_s1_trace(asset: dict[str, Any]) -> dict[str, Any]:
    provisions = derive_candidate_provisions(asset)
    return {
        "scenario": "S1",
        "inputAsset": asset["assetId"],
        "transactionType": asset["transactionType"],
        "candidateProvisions": provisions,
        "conflictResolution": [
            {
                "tier": "Tier 1",
                "rule": "lex-specialis",
                "status": "not_applicable",
                "reason": "S1 has no competing general-versus-special provision conflict after pseudonymized flow selection.",
            },
            {
                "tier": "Tier 2",
                "rule": "stricter-wins",
                "status": "not_applicable",
                "reason": "S1 has no same-specificity conflict requiring risk ordering.",
            },
        ],
        "selectedTemplates": ["templates/pipa-28-2-pseudonymized-research.ttl"],
        "generatedPolicy": "templates/pipa-28-2-pseudonymized-research.ttl",
        "complianceLevel": "L2",
        "authorizationRecord": "examples/legal-basis-record/s1-valid.json",
        "expectedRuntime": {
            "allow": ["odrl:use", "kr:process-in-safe-area"],
            "block": ["kr:re-identify"],
            "transferRightApplicable": False,
        },
    }


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    asset = load_json(root / "examples/s1-decision-trace/input.asset.json")
    print(json.dumps(build_s1_trace(asset), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
