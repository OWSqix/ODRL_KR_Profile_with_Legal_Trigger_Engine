from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROVIDER_MANAGEMENT = "http://localhost:19193/management/v3"
CONSUMER_MANAGEMENT = "http://localhost:29193/management/v3"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def request_json(method: str, url: str, body: dict[str, Any] | None = None) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(url, data=data, method=method)
    request.add_header("content-type", "application/json")
    request.add_header("accept", "application/json")
    try:
        with urlopen(request, timeout=15) as response:
            payload = response.read().decode("utf-8")
            if not payload:
                return {}
            return json.loads(payload)
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed with HTTP {error.code}: {details}") from error
    except URLError as error:
        raise RuntimeError(f"{method} {url} failed: {error}") from error


def post_json(url: str, body: dict[str, Any]) -> Any:
    return request_json("POST", url, body)


def post_json_retry(url: str, body: dict[str, Any]) -> Any:
    last_error: Exception | None = None
    for _ in range(30):
        try:
            return post_json(url, body)
        except RuntimeError as error:
            last_error = error
            message = str(error)
            if "HTTP 404" not in message and "HTTP 405" not in message and "HTTP 503" not in message:
                raise
            time.sleep(0.5)
    raise RuntimeError(f"POST did not become ready: {url}") from last_error


def get_json(url: str) -> Any:
    return request_json("GET", url)


def extract_dataset(catalog: dict[str, Any]) -> dict[str, Any]:
    dataset = catalog.get("dcat:dataset") or catalog.get("dataset")
    if isinstance(dataset, list):
        if not dataset:
            raise AssertionError("Catalog contains no datasets.")
        return dataset[0]
    if isinstance(dataset, dict):
        return dataset
    raise AssertionError(f"Catalog dataset missing or unexpected: {catalog}")


def extract_offer(dataset: dict[str, Any]) -> dict[str, Any]:
    policy = dataset.get("odrl:hasPolicy") or dataset.get("hasPolicy")
    if isinstance(policy, list):
        if not policy:
            raise AssertionError("Dataset contains no contract offers.")
        return policy[0]
    if isinstance(policy, dict):
        return policy
    raise AssertionError(f"Dataset policy missing or unexpected: {dataset}")


def identifier(document: dict[str, Any]) -> str:
    value = document.get("@id") or document.get("id")
    if not isinstance(value, str) or not value:
        raise AssertionError(f"Identifier missing: {document}")
    return value


def poll_negotiation(negotiation_id: str) -> dict[str, Any]:
    terminal = {"FINALIZED", "TERMINATED", "ERROR"}
    last = {}
    for _ in range(80):
        last = get_json(f"{CONSUMER_MANAGEMENT}/contractnegotiations/{negotiation_id}")
        state = last.get("state") or last.get("stateName")
        if state in terminal:
            return last
        time.sleep(0.5)
    raise TimeoutError(f"Negotiation did not reach a terminal state: {last}")


def poll_transfer(transfer_process_id: str) -> dict[str, Any]:
    terminal = {"STARTED", "COMPLETED", "TERMINATED", "ERROR"}
    last = {}
    for _ in range(80):
        last = get_json(f"{CONSUMER_MANAGEMENT}/transferprocesses/{transfer_process_id}")
        state = last.get("state") or last.get("stateName")
        if state in terminal:
            return last
        time.sleep(0.5)
    raise TimeoutError(f"Transfer process did not reach a retrievable state: {last}")


def poll_edr_data_address(transfer_process_id: str) -> dict[str, Any]:
    last_error: Exception | None = None
    for _ in range(80):
        try:
            edr = get_json(f"{CONSUMER_MANAGEMENT}/edrs/{transfer_process_id}/dataaddress")
            if edr:
                return edr
        except RuntimeError as error:
            last_error = error
            if "HTTP 404" not in str(error):
                raise
        time.sleep(0.5)
    raise TimeoutError(f"EDR data address did not become available for {transfer_process_id}") from last_error


def find_value(document: dict[str, Any], *names: str) -> Any:
    for name in names:
        for key in (name, f"edc:{name}", f"https://w3id.org/edc/v0.0.1/ns/{name}"):
            if key in document:
                return document[key]
    properties = document.get("properties")
    if isinstance(properties, dict):
        for name in names:
            for key in (name, f"edc:{name}", f"https://w3id.org/edc/v0.0.1/ns/{name}"):
                if key in properties:
                    return properties[key]
    return None


def retrieve_payload(edr: dict[str, Any]) -> str:
    endpoint = find_value(edr, "endpoint", "baseUrl")
    auth_key = find_value(edr, "authKey", "authorization")
    auth_code = find_value(edr, "authCode", "authCodeId")
    if not endpoint:
        raise AssertionError(f"EDR endpoint missing: {edr}")
    print(json.dumps({"edrEndpoint": endpoint, "hasAuthToken": bool(auth_key or auth_code)}, indent=2))
    request = Request(str(endpoint), method="GET")
    if auth_key and auth_code:
        request.add_header(str(auth_key), str(auth_code))
    elif auth_key:
        request.add_header("Authorization", str(auth_key))
    elif auth_code:
        request.add_header("Authorization", str(auth_code))
    try:
        with urlopen(request, timeout=20) as response:
            payload = response.read().decode("utf-8")
            if response.status >= 400:
                raise RuntimeError(f"Payload retrieval failed: HTTP {response.status} {payload}")
            return payload
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Payload retrieval failed: HTTP {error.code} {details}") from error


def assert_payload_is_protected(edr: dict[str, Any]) -> None:
    endpoint = find_value(edr, "endpoint", "baseUrl")
    if not endpoint:
        raise AssertionError(f"EDR endpoint missing: {edr}")

    for label, request in (
        ("missing-token", Request(str(endpoint), method="GET")),
        ("invalid-token", Request(str(endpoint), method="GET", headers={"Authorization": "invalid-token"})),
    ):
        try:
            with urlopen(request, timeout=20) as response:
                raise AssertionError(f"{label} unexpectedly succeeded with HTTP {response.status}")
        except HTTPError as error:
            if label == "missing-token":
                assert error.code == 401, (label, error.code, error.read().decode("utf-8", errors="replace"))
            else:
                assert error.code == 403, (label, error.code, error.read().decode("utf-8", errors="replace"))


def main() -> int:
    root = Path(sys.argv[1])
    resources = root / "resources"

    post_json_retry(f"{PROVIDER_MANAGEMENT}/assets", load_json(resources / "create-asset.json"))
    post_json_retry(f"{PROVIDER_MANAGEMENT}/policydefinitions", load_json(resources / "create-policy.json"))
    post_json_retry(
        f"{PROVIDER_MANAGEMENT}/contractdefinitions",
        load_json(resources / "create-contract-definition.json"),
    )

    catalog = post_json_retry(f"{CONSUMER_MANAGEMENT}/catalog/request", load_json(resources / "fetch-catalog.json"))
    dataset = extract_dataset(catalog)
    offer = extract_offer(dataset)
    offer_id = identifier(offer)

    negotiate = {
        "@context": {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"},
        "@type": "ContractRequest",
        "counterPartyId": "provider",
        "counterPartyAddress": "http://localhost:19194/protocol/2025-1",
        "protocol": "dataspace-protocol-http:2025-1",
        "policy": {
            "@context": "http://www.w3.org/ns/odrl.jsonld",
            "@id": offer_id,
            "@type": "Offer",
            "assigner": "provider",
            "target": "s1-broadcast-viewing-log",
        },
    }
    negotiation = post_json_retry(f"{CONSUMER_MANAGEMENT}/contractnegotiations", negotiate)
    negotiation_id = identifier(negotiation)
    final_negotiation = poll_negotiation(negotiation_id)

    assert final_negotiation.get("state") == "FINALIZED", final_negotiation
    agreement_id = final_negotiation.get("contractAgreementId")
    assert agreement_id, final_negotiation
    time.sleep(3)

    transfer_request = {
        "@context": {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"},
        "@type": "TransferRequest",
        "counterPartyAddress": "http://localhost:19194/protocol/2025-1",
        "contractId": agreement_id,
        "assetId": "s1-broadcast-viewing-log",
        "protocol": "dataspace-protocol-http:2025-1",
        "transferType": "HttpData-PULL",
        "dataDestination": {
            "@type": "DataAddress",
            "type": "HttpProxy"
        }
    }
    transfer = post_json_retry(f"{CONSUMER_MANAGEMENT}/transferprocesses", transfer_request)
    transfer_process_id = identifier(transfer)
    final_transfer = poll_transfer(transfer_process_id)
    transfer_state = final_transfer.get("state")
    assert transfer_state in {"STARTED", "COMPLETED"}, final_transfer

    edr = poll_edr_data_address(transfer_process_id)
    assert_payload_is_protected(edr)
    payload = retrieve_payload(edr)
    assert "Leanne Graham" in payload or "Bret" in payload, payload[:500]

    print(
        json.dumps(
            {
                "datasetId": identifier(dataset),
                "contractOfferId": offer_id,
                "contractNegotiationId": negotiation_id,
                "contractAgreementId": agreement_id,
                "state": final_negotiation.get("state"),
                "transferProcessId": transfer_process_id,
                "transferState": transfer_state,
                "payloadBytes": len(payload.encode("utf-8")),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
