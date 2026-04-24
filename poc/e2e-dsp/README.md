# DSP E2E Verification

This directory contains a local two-connector Eclipse EDC 0.17.0 DSP test.

## What It Does

`scripts/run_dsp_e2e.sh`:

1. Installs the local ODRL-KR EDC extension into the Maven local repository.
2. Builds `control-plane/target/control-plane.jar`, a shaded EDC control-plane runtime.
3. Generates ephemeral RSA test keys under `target/configuration/`.
4. Starts a provider control plane and a consumer control plane.
5. Starts a provider custom data plane and a consumer custom data plane.
6. Seeds the provider through Management API:
   - asset: `s1-broadcast-viewing-log`
   - policy: `s1-odrl-kr-policy`
   - contract definition: `s1-contract-definition`
7. Requests the provider catalog from the consumer control plane over DSP.
8. Starts contract negotiation from the consumer control plane.
9. Polls until the negotiation reaches `FINALIZED`.
10. Starts `HttpData-PULL` transfer.
11. Retrieves the EDR data address.
12. Verifies unauthenticated and invalid-token payload requests are rejected.
13. Performs authenticated payload retrieval from the standalone custom data plane endpoint.
14. Starts `HttpData-PUSH` transfer to the consumer custom data-plane sink and verifies the pushed payload is stored.

## Run

From the repository root:

```bash
poc/e2e-dsp/scripts/run_dsp_e2e.sh
```

The script cleans up all Java and Python runtime processes on exit. Runtime logs are written under `poc/e2e-dsp/target/logs/`.

The orchestration client uses EDC Management API `v4` for asset/policy/catalog/negotiation/transfer operations. EDR lookup is served by the local authenticated helper endpoint at the consumer public port, so the DSP smoke test no longer depends on the deprecated EDR cache `v3` management API.

## Scope

This is a local DSP catalog + contract-negotiation + transfer + EDR + protected payload retrieval E2E test.

The protected payload endpoint is now served by the standalone custom data plane. For consumer-pull it creates an EDR-like `DataAddress`, enforces a simple bearer-style token on `/public/{transferId}`, and proxies the configured upstream `HttpData` source. The control-plane extension still serves helper endpoints on the public port for local EDR/source lookup, but the data transfer itself is no longer executed by an embedded/classic EDC data plane. This remains a PoC implementation, not a hardened production data-plane distribution.
