import json
from pathlib import Path

from rdflib import Graph, URIRef

from odrl_kr.lte import build_s1_trace, load_json


ROOT = Path(__file__).resolve().parents[1]


def test_s1_lte_trace_matches_expected_fixture():
    asset = load_json(ROOT / "examples/s1-decision-trace/input.asset.json")
    expected = load_json(ROOT / "examples/s1-decision-trace/expected.trace.json")
    assert build_s1_trace(asset) == expected


def test_s1_trace_has_required_proof_path():
    asset = load_json(ROOT / "examples/s1-decision-trace/input.asset.json")
    trace = build_s1_trace(asset)
    assert trace["candidateProvisions"] == [
        "kr:PIPA-28-2",
        "kr:PIPA-28-4",
        "kr:PIPA-28-5",
        "kr:PIPA-28-7",
    ]
    assert trace["conflictResolution"][0]["status"] == "not_applicable"
    assert trace["expectedRuntime"]["transferRightApplicable"] is False


def test_s1_trace_is_json_serializable():
    asset = load_json(ROOT / "examples/s1-decision-trace/input.asset.json")
    serialized = json.dumps(build_s1_trace(asset), sort_keys=True)
    assert "kr:PIPA-28-2" in serialized


def test_s1_trace_references_existing_artifacts():
    asset = load_json(ROOT / "examples/s1-decision-trace/input.asset.json")
    trace = build_s1_trace(asset)

    for path_key in ("generatedPolicy", "authorizationRecord"):
        assert (ROOT / trace[path_key]).is_file()
    for template in trace["selectedTemplates"]:
        assert (ROOT / template).is_file()


def test_s1_trace_policy_and_legal_basis_record_are_consistent():
    asset = load_json(ROOT / "examples/s1-decision-trace/input.asset.json")
    trace = build_s1_trace(asset)
    record = load_json(ROOT / trace["authorizationRecord"])["credentialSubject"]

    policy_graph = Graph()
    policy_graph.parse(ROOT / trace["generatedPolicy"])

    right_operands = set(
        str(value)
        for value in policy_graph.objects(None, URIRef("http://www.w3.org/ns/odrl/2/rightOperand"))
    )

    assert "https://w3id.org/odrl-kr#PIPA-28-2" in right_operands
    assert "https://w3id.org/odrl-kr#PIPA-28-5" in right_operands
    assert record["applicableProvisions"]["lawfulProcessingBasis"] in trace["candidateProvisions"]
    assert set(record["applicableProvisions"]["prohibitionRules"]).issubset(trace["candidateProvisions"])
    assert set(record["applicableProvisions"]["rightsExclusionRules"]).issubset(trace["candidateProvisions"])
