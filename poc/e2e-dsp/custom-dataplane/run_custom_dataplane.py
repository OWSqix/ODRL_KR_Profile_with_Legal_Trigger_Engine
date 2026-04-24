#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import secrets
import sys
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


EDC_CONTEXT = {"@vocab": "https://w3id.org/edc/v0.0.1/ns/"}
EDC_BASE_URL = "https://w3id.org/edc/v0.0.1/ns/baseUrl"
EDC_ENDPOINT = "https://w3id.org/edc/v0.0.1/ns/endpoint"


@dataclass
class PullGrant:
    source_url: str
    auth_token: str


class CustomDataPlane:
    def __init__(self, *, participant_id: str, component_id: str, host: str, port: int,
                 control_plane_control_url: str, public_base_url: str,
                 source_lookup_base_url: str | None = None,
                 default_source_url: str | None = None,
                 log_file: Path | None = None) -> None:
        self.participant_id = participant_id
        self.component_id = component_id
        self.host = host
        self.port = port
        self.control_plane_control_url = control_plane_control_url.rstrip("/")
        self.public_base_url = public_base_url.rstrip("/")
        self.source_lookup_base_url = source_lookup_base_url.rstrip("/") if source_lookup_base_url else None
        self.default_source_url = default_source_url
        self.log_file = log_file
        self.pull_grants: dict[str, PullGrant] = {}
        self.push_sinks: dict[str, bytes] = {}
        self.server = ThreadingHTTPServer((host, port), self._handler())

    def _log(self, message: str) -> None:
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n"
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            self.log_file.write_text(
                (self.log_file.read_text() if self.log_file.exists() else "") + line,
                encoding="utf-8",
            )
        else:
            sys.stderr.write(line)

    def _request_json(self, method: str, url: str, body: dict[str, Any] | None = None) -> Any:
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(url, data=data, method=method)
        request.add_header("content-type", "application/json")
        request.add_header("accept", "application/json")
        with urlopen(request, timeout=20) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload) if payload else {}

    @staticmethod
    def _extract_url(document: dict[str, Any]) -> str | None:
        direct = (
            document.get("baseUrl")
            or document.get("endpoint")
            or document.get(EDC_BASE_URL)
            or document.get(EDC_ENDPOINT)
        )
        if direct:
            return direct

        for item in document.get("endpointProperties", []) or []:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            value = item.get("value")
            if name in {"baseUrl", "endpoint", EDC_BASE_URL, EDC_ENDPOINT} and value:
                return value
        return None

    def register(self) -> None:
        registration = {
            "@context": EDC_CONTEXT,
            "@type": "DataPlaneInstance",
            "@id": self.component_id,
            "url": f"http://{self.host}:{self.port}/dataflows",
            "allowedSourceTypes": ["HttpData"],
            "allowedTransferTypes": ["HttpData-PULL", "HttpData-PUSH"],
        }
        last_error: Exception | None = None
        for _ in range(40):
            try:
                self._request_json("POST", f"{self.control_plane_control_url}/dataplanes", registration)
                break
            except HTTPError as exc:
                last_error = exc
                if exc.code not in {404, 405, 503}:
                    raise
                time.sleep(0.5)
            except URLError as exc:
                last_error = exc
                time.sleep(0.5)
        else:
            raise RuntimeError(f"dataplane registration failed: {last_error}") from last_error
        self._log(f"registered dataplane {self.component_id} at {registration['url']}")

    def serve_forever(self) -> None:
        self.server.serve_forever()

    def _handler(self):
        outer = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "ODRLKRCustomDataPlane/0.1"

            def log_message(self, fmt: str, *args: Any) -> None:
                outer._log(fmt % args)

            def do_GET(self) -> None:
                path = urlparse(self.path).path
                if path == "/dataflows/check":
                    self._write_json(200, {})
                    return
                if path.startswith("/public/"):
                    transfer_id = path.removeprefix("/public/")
                    outer._handle_public_pull(self, transfer_id)
                    return
                if path.startswith("/sinks/"):
                    outer._handle_sink_read(self, path.removeprefix("/sinks/"))
                    return
                self._write_text(404, "Not Found")

            def do_POST(self) -> None:
                path = urlparse(self.path).path
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = 0
                raw = self.rfile.read(length) if length else b"{}"
                payload = json.loads(raw.decode("utf-8") or "{}")

                if path == "/dataflows/prepare":
                    self._write_json(200, {"state": "PREPARED"})
                    return
                if path == "/dataflows/start":
                    outer._handle_start(self, payload)
                    return
                if path.startswith("/dataflows/") and path.endswith("/started"):
                    self._write_json(200, {"acknowledged": "started"})
                    return
                if path.startswith("/dataflows/") and path.endswith("/completed"):
                    self._write_json(200, {"acknowledged": "completed"})
                    return
                if path.startswith("/dataflows/") and path.endswith("/terminate"):
                    self._write_json(200, {"acknowledged": "terminated"})
                    return
                if path.startswith("/sinks/"):
                    sink_id = path.removeprefix("/sinks/")
                    outer.push_sinks[sink_id] = raw
                    outer._log(f"stored push sink {sink_id} bytes={len(raw)}")
                    self._write_json(200, {"stored": True, "bytes": len(raw)})
                    return
                self._write_text(404, "Not Found")

            def _write_json(self, status: int, body: dict[str, Any]) -> None:
                encoded = json.dumps(body).encode("utf-8")
                self.send_response(status)
                self.send_header("content-type", "application/json; charset=utf-8")
                self.send_header("content-length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def _write_text(self, status: int, body: str) -> None:
                encoded = body.encode("utf-8")
                self.send_response(status)
                self.send_header("content-type", "text/plain; charset=utf-8")
                self.send_header("content-length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

        return Handler

    def _handle_start(self, handler: BaseHTTPRequestHandler, payload: dict[str, Any]) -> None:
        self._log(f"start payload: {json.dumps(payload, sort_keys=True)}")
        transfer_type = payload.get("transferType", "")
        process_id = payload.get("processId")
        data_address = payload.get("dataAddress") or {}
        source_url = None if transfer_type.endswith("PUSH") else self._extract_url(data_address)

        if not source_url and self.source_lookup_base_url:
            dataset_id = payload.get("datasetId")
            if dataset_id:
                try:
                    source_lookup = self._request_json(
                        "GET",
                        f"{self.source_lookup_base_url}/assets/{dataset_id}/source-data-address",
                    )
                    source_url = self._extract_url(source_lookup)
                except Exception as exc:  # noqa: BLE001
                    self._log(f"asset source lookup failed for {dataset_id}: {exc}")
        if not source_url and self.source_lookup_base_url:
            try:
                source_lookup = self._request_json(
                    "GET",
                    f"{self.source_lookup_base_url}/transfers/{process_id}/source-data-address",
                )
                source_url = self._extract_url(source_lookup)
            except Exception as exc:  # noqa: BLE001
                self._log(f"source lookup failed for {process_id}: {exc}")
        if transfer_type.endswith("PUSH") and (not source_url or source_url == self._extract_url(data_address)):
            source_url = self.default_source_url or source_url

        if not process_id:
            handler.send_error(400, "processId missing")
            return

        if transfer_type.endswith("PULL"):
            if not source_url:
                handler.send_error(400, "source endpoint missing")
                return
            token = secrets.token_urlsafe(24)
            self.pull_grants[process_id] = PullGrant(source_url=source_url, auth_token=token)
            response = {
                "state": "STARTED",
                "dataAddress": {
                    "endpointType": "HttpData",
                    "endpoint": f"{self.public_base_url}/{process_id}",
                    "endpointProperties": [
                        {"name": "authKey", "value": "Authorization"},
                        {"name": "authCode", "value": token},
                    ],
                },
            }
            handler.send_response(200)
            encoded = json.dumps(response).encode("utf-8")
            handler.send_header("content-type", "application/json; charset=utf-8")
            handler.send_header("content-length", str(len(encoded)))
            handler.end_headers()
            handler.wfile.write(encoded)
            return

        if transfer_type.endswith("PUSH"):
            destination = self._extract_url(data_address)
            if not source_url or not destination:
                handler.send_error(400, "source or destination endpoint missing")
                return
            thread = threading.Thread(
                target=self._run_push_transfer,
                args=(payload, process_id, source_url, destination),
                daemon=True,
            )
            thread.start()
            encoded = json.dumps({"state": "STARTING"}).encode("utf-8")
            handler.send_response(200)
            handler.send_header("content-type", "application/json; charset=utf-8")
            handler.send_header("content-length", str(len(encoded)))
            handler.end_headers()
            handler.wfile.write(encoded)
            return

        handler.send_error(400, f"Unsupported transferType: {transfer_type}")

    def _notify_started(self, callback_address: str | None, process_id: str, response: dict[str, Any]) -> None:
        if not callback_address:
            return
        try:
            body = {
                "state": response["state"],
                "dataAddress": response.get("dataAddress"),
            }
            self._log(f"notify started {process_id} -> {callback_address}")
            self._request_json("POST", f"{callback_address.rstrip('/')}/transfers/{process_id}/dataflow/started", body)
        except Exception as exc:  # noqa: BLE001
            self._log(f"started callback failed for {process_id}: {exc}")

    def _notify_completed(self, callback_address: str | None, process_id: str) -> None:
        if not callback_address:
            return
        try:
            self._log(f"notify completed {process_id} -> {callback_address}")
            request = Request(
                f"{callback_address.rstrip('/')}/transfers/{process_id}/dataflow/completed",
                data=b"",
                method="POST",
            )
            request.add_header("content-type", "application/json")
            with urlopen(request, timeout=20):
                pass
        except Exception as exc:  # noqa: BLE001
            self._log(f"completed callback failed for {process_id}: {exc}")

    def _notify_errored(self, callback_address: str | None, process_id: str, error: str) -> None:
        if not callback_address:
            return
        try:
            self._request_json(
                "POST",
                f"{callback_address.rstrip('/')}/transfers/{process_id}/dataflow/errored",
                {"state": "ERRORED", "error": error},
            )
        except Exception as exc:  # noqa: BLE001
            self._log(f"errored callback failed for {process_id}: {exc}")

    def _run_push_transfer(self, payload: dict[str, Any], process_id: str, source_url: str, destination_url: str) -> None:
        callback = payload.get("callbackAddress")
        try:
            self._log(f"push transfer {process_id} source={source_url} destination={destination_url}")
            self._notify_started(callback, process_id, {"state": "STARTED"})
            with urlopen(source_url, timeout=30) as source_response:
                content_type = source_response.headers.get("content-type", "application/octet-stream")
                body = source_response.read()
            request = Request(destination_url, data=body, method="POST")
            request.add_header("content-type", content_type)
            with urlopen(request, timeout=30):
                pass
            self._log(f"push transfer delivered {process_id} bytes={len(body)}")
        except Exception as exc:  # noqa: BLE001
            self._log(f"push transfer failed {process_id} source={source_url} destination={destination_url}: {exc}")
            self._notify_errored(callback, process_id, str(exc))

    def _handle_public_pull(self, handler: BaseHTTPRequestHandler, transfer_id: str) -> None:
        grant = self.pull_grants.get(transfer_id)
        if grant is None:
            handler.send_error(404, "Unknown transfer")
            return

        token = handler.headers.get("Authorization")
        if token is None or token == "":
            handler.send_error(401, "Missing Authorization token.")
            return
        if token != grant.auth_token:
            handler.send_error(403, "Invalid Authorization token.")
            return

        try:
            with urlopen(grant.source_url, timeout=30) as upstream:
                body = upstream.read()
                content_type = upstream.headers.get("content-type", "application/octet-stream")
                handler.send_response(upstream.status)
                handler.send_header("content-type", content_type)
                handler.send_header("content-length", str(len(body)))
                handler.end_headers()
                handler.wfile.write(body)
        except HTTPError as exc:
            handler.send_error(exc.code, exc.reason)
        except URLError as exc:
            handler.send_error(502, str(exc.reason))

    def _handle_sink_read(self, handler: BaseHTTPRequestHandler, sink_id: str) -> None:
        body = self.push_sinks.get(sink_id)
        if body is None:
            handler.send_error(404, "Unknown sink")
            return
        handler.send_response(200)
        handler.send_header("content-type", "application/json; charset=utf-8")
        handler.send_header("content-length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--participant-id", required=True)
    parser.add_argument("--component-id", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--control-plane-control-url", required=True)
    parser.add_argument("--public-base-url", required=True)
    parser.add_argument("--source-lookup-base-url")
    parser.add_argument("--default-source-url")
    parser.add_argument("--log-file")
    args = parser.parse_args()

    dataplane = CustomDataPlane(
        participant_id=args.participant_id,
        component_id=args.component_id,
        host=args.host,
        port=args.port,
        control_plane_control_url=args.control_plane_control_url,
        public_base_url=args.public_base_url,
        source_lookup_base_url=args.source_lookup_base_url,
        default_source_url=args.default_source_url,
        log_file=Path(args.log_file) if args.log_file else None,
    )
    dataplane.register()
    dataplane.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
