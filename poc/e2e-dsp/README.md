# DSP E2E Verification

This directory contains a local two-connector Eclipse EDC 0.16.0 DSP test.

## What It Does

`scripts/run_dsp_e2e.sh`:

1. Installs the local ODRL-KR EDC extension into the Maven local repository.
2. Builds `connector/target/connector.jar`, a shaded EDC connector runtime.
3. Generates ephemeral RSA test keys under `target/configuration/`.
4. Starts a provider connector and a consumer connector.
5. Seeds the provider through Management API:
   - asset: `s1-broadcast-viewing-log`
   - policy: `s1-odrl-kr-policy`
   - contract definition: `s1-contract-definition`
6. Requests the provider catalog from the consumer connector over DSP.
7. Starts contract negotiation from the consumer.
8. Polls until the negotiation reaches `FINALIZED`.
9. Starts `HttpData-PULL` transfer.
10. Retrieves the EDR data address.
11. Verifies unauthenticated and invalid-token payload requests are rejected.
12. Performs authenticated payload retrieval from the provider public endpoint.

## Run

From the repository root:

```bash
poc/e2e-dsp/scripts/run_dsp_e2e.sh
```

The script cleans up both Java connector processes on exit. Runtime logs are written under `poc/e2e-dsp/target/logs/`.

## Scope

This is a local DSP catalog + contract-negotiation + transfer + EDR + protected payload retrieval E2E test.

The public payload endpoint is an authenticated local EDC extension endpoint. It uses EDC `DataPlaneAuthorizationService` to validate the EDR token, resolves the authorized source `DataAddress`, and proxies the configured `baseUrl`. The E2E test also verifies missing and invalid tokens are rejected before successful authenticated retrieval. EDC `0.16.0` no longer publishes the legacy `data-plane-public-api` artifact, so this endpoint provides the minimal local public API surface needed for connector-level verification. It is not a hardened production data-plane distribution.
