# EDC 0.17.0-Based Extension

The manuscript targets Eclipse EDC 0.17.0 PolicyEngine extension behavior. Current EDC documentation describes policy evaluation as extension code registered as policy functions, where functions evaluate an operator, right operand, rule, and policy context.

This repository now compiles against the actual Eclipse EDC 0.17.0 artifacts published to Maven Central:

- `org.eclipse.edc:policy-engine-spi:0.17.0`
- `org.eclipse.edc:policy-engine-lib:0.17.0`
- `org.eclipse.edc:policy-model:0.17.0`
- `org.eclipse.edc:boot-spi:0.17.0`
- `org.eclipse.edc:runtime-metamodel:0.17.0`

`KoreaPolicyExtension` is a real `ServiceExtension` registered through `META-INF/services/org.eclipse.edc.spi.system.ServiceExtension`. It binds ODRL-KR actions and left operands to negotiation and transfer scopes, then registers concrete `AtomicConstraintRuleFunction` implementations for:

- legal basis equality against an active AuthorizationRecord,
- pseudonymization rank comparison,
- safe-area processing duty,
- re-identification prohibition.

The tests instantiate EDC 0.17.0 `PolicyEngineImpl`, `RuleBindingRegistryImpl`, `ScopeFilter`, and `RuleValidator` from EDC artifacts and evaluate S1 allow/block behavior through registered ODRL-KR functions.

For the local two-connector DSP runtime, the PoC adds one small participant-context compatibility extension:

- `SingleParticipantContextCompatibilityExtension` supplies the single-participant context/config services still expected by EDC 0.17.0 connector APIs.

This is still a proof-of-concept extension, not a production EDC connector distribution. Production use still needs connector packaging, operational configuration, audit persistence, external AuthorizationRecord verification, and legal review.
