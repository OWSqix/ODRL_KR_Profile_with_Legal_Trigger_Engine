# Release Notes v0.2.0

Release date: 2026-04-24

## Summary

This release promotes the PoC from the public `v0.1.0` proof-background baseline to an `EDC 0.17.0`-validated supplement with a separated custom data-plane path for DSP runtime verification.

## Highlights

- Migrated the proof background from `EDC 0.16.0` assumptions to `EDC 0.17.0`.
- Split DSP runtime verification into:
  - shaded control-plane runtime under `e2e-dsp/control-plane/`
  - standalone custom HTTP data plane under `e2e-dsp/custom-dataplane/`
- Removed the DSP smoke test's dependence on the deprecated EDR cache `management/v3` API.
- Verified both `HttpData-PULL` and `HttpData-PUSH` flows in the local DSP E2E path.
- Added runtime-only compatibility support for `SingleParticipantContextSupplier` and related single-participant config gaps still present in the published `EDC 0.17.x` module set.

## Validation Snapshot

- `poc/scripts/run_all_tests.sh` -> pass
- `poc/scripts/run_e2e.sh` -> pass
- `poc/e2e-dsp/scripts/run_dsp_e2e.sh` -> pass
- Latest DSP E2E observed:
  - negotiation `FINALIZED`
  - pull transfer `STARTED`
  - push transfer `STARTED`
  - `payloadBytes=5645`
  - `pushPayloadBytes=5645`

## Scope Notes

- This release remains a research PoC and proof-background supplement.
- The standalone custom data plane is intentionally minimal and not production-hardened.
- The only remaining compatibility boundary is the runtime shim around EDC `0.17.x` single-participant participant-context internals.
