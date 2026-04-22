package org.odrlkr.edc;

import org.eclipse.edc.policy.engine.PolicyEngineImpl;
import org.eclipse.edc.policy.engine.RuleBindingRegistryImpl;
import org.eclipse.edc.policy.engine.ScopeFilter;
import org.eclipse.edc.policy.engine.validation.RuleValidator;
import org.eclipse.edc.policy.model.Action;
import org.eclipse.edc.policy.model.AtomicConstraint;
import org.eclipse.edc.policy.model.Duty;
import org.eclipse.edc.policy.model.LiteralExpression;
import org.eclipse.edc.policy.model.Operator;
import org.eclipse.edc.policy.model.Permission;
import org.eclipse.edc.policy.model.Policy;
import org.eclipse.edc.policy.model.Prohibition;
import org.eclipse.edc.spi.system.ServiceExtension;
import org.junit.jupiter.api.Test;

import java.util.ServiceLoader;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.odrlkr.edc.KoreaPolicyConstants.ACTION_PSEUDONYMIZE;
import static org.odrlkr.edc.KoreaPolicyConstants.ACTION_REIDENTIFY;
import static org.odrlkr.edc.KoreaPolicyConstants.ACTION_USE;
import static org.odrlkr.edc.KoreaPolicyConstants.KR_LEGAL_BASIS;
import static org.odrlkr.edc.KoreaPolicyConstants.KR_PSEUDONYMIZATION_LEVEL;
import static org.odrlkr.edc.KoreaPolicyConstants.KR_REFERENCE_LAW;
import static org.odrlkr.edc.KoreaPolicyConstants.KR_SAFE_AREA_PROCESSING;
import static org.odrlkr.edc.KoreaPolicyConstants.PIPA_28_2;
import static org.odrlkr.edc.KoreaPolicyConstants.PIPA_28_5;
import static org.odrlkr.edc.KoreaPolicyConstants.PSEUDONYMIZATION_LEVEL_2;
import static org.odrlkr.edc.KoreaPolicyConstants.SCOPE_NEGOTIATION;

public final class KoreaPolicyFunctionTest {
    @Test
    void legalBasisFunctionAllowsS1AndBlocksMismatch() {
        var record = AuthorizationRecord.s1();
        var service = new InMemoryRecordVerificationService();
        service.put("s1-valid", record);
        service.put("wrong-basis", record.withLegalBasis("kr:PIPA-15"));
        var function = new LegalBasisPermissionFunction(service);

        assertTrue(function.evaluate(Operator.EQ, PIPA_28_2, permission(), context("s1-valid")));
        assertFalse(function.evaluate(Operator.EQ, PIPA_28_2, permission(), context("wrong-basis")));
    }

    @Test
    void pseudonymizationRankFunctionAllowsLevelTwoAndBlocksLevelOne() {
        var record = AuthorizationRecord.s1();
        var service = new InMemoryRecordVerificationService();
        service.put("level-two", record);
        service.put("level-one", record.withPseudonymizationRank(1));
        var function = new PseudonymizationDutyFunction(service);

        assertTrue(function.evaluate(Operator.GEQ, PSEUDONYMIZATION_LEVEL_2, duty(), context("level-two")));
        assertFalse(function.evaluate(Operator.GEQ, PSEUDONYMIZATION_LEVEL_2, duty(), context("level-one")));
    }

    @Test
    void safeAreaFunctionAllowsS1AndBlocksMissingSafeArea() {
        var service = new InMemoryRecordVerificationService();
        service.put("s1-valid", AuthorizationRecord.s1());
        service.put("missing-safe-area", AuthorizationRecord.s1().withoutSafeAreaProcessing());
        var function = new SafeAreaPermissionFunction(service);

        assertTrue(function.evaluate(Operator.EQ, true, permission(), context("s1-valid")));
        assertFalse(function.evaluate(Operator.EQ, true, permission(), context("missing-safe-area")));
    }

    @Test
    void reidentificationProhibitionIsDetected() {
        var service = InMemoryRecordVerificationService.withS1Record();
        var function = new ReferenceLawProhibitionFunction(service);

        assertTrue(function.evaluate(Operator.EQ, PIPA_28_5, prohibition(), context("s1-valid")));
        assertFalse(KoreaPolicyFunctions.actionAllowed(AuthorizationRecord.s1(), ACTION_REIDENTIFY),
                "PIPA-28-5 prohibition must block re-identification");
        assertTrue(KoreaPolicyFunctions.actionAllowed(AuthorizationRecord.s1(), ACTION_USE),
                "ODRL use should remain allowed for active S1 record");
    }

    @Test
    void edcPolicyEngineEvaluatesRegisteredS1PermissionAndDutyFunctions() {
        var service = InMemoryRecordVerificationService.withS1Record();
        var registry = new RuleBindingRegistryImpl();
        var engine = new PolicyEngineImpl(new ScopeFilter(registry), new RuleValidator(registry));
        KoreaPolicyExtension.register(registry, engine, service);

        var policy = Policy.Builder.newInstance()
                .permission(Permission.Builder.newInstance()
                        .action(action(ACTION_USE))
                        .constraint(constraint(KR_LEGAL_BASIS, Operator.EQ, PIPA_28_2))
                        .constraint(constraint(KR_SAFE_AREA_PROCESSING, Operator.EQ, true))
                        .build())
                .duty(Duty.Builder.newInstance()
                        .action(action(ACTION_PSEUDONYMIZE))
                        .constraint(constraint(KR_PSEUDONYMIZATION_LEVEL, Operator.GEQ, PSEUDONYMIZATION_LEVEL_2))
                        .build())
                .build();

        var result = engine.evaluate(policy, context("s1-valid"));
        assertTrue(result.succeeded(), result::getFailureDetail);
    }

    @Test
    void edcPolicyEngineFailsWhenLegalBasisDoesNotMatch() {
        var service = new InMemoryRecordVerificationService();
        service.put("wrong-basis", AuthorizationRecord.s1().withLegalBasis("kr:PIPA-15"));
        var registry = new RuleBindingRegistryImpl();
        var engine = new PolicyEngineImpl(new ScopeFilter(registry), new RuleValidator(registry));
        KoreaPolicyExtension.register(registry, engine, service);

        var policy = Policy.Builder.newInstance()
                .permission(Permission.Builder.newInstance()
                        .action(action(ACTION_USE))
                        .constraint(constraint(KR_LEGAL_BASIS, Operator.EQ, PIPA_28_2))
                        .build())
                .build();

        var result = engine.evaluate(policy, context("wrong-basis"));
        assertTrue(result.failed(), "EDC policy engine should fail a mismatched legal basis.");
    }

    @Test
    void registeredBindingsCoverNegotiationAndTransferScopes() {
        var registry = new RuleBindingRegistryImpl();
        var engine = new PolicyEngineImpl(new ScopeFilter(registry), new RuleValidator(registry));
        KoreaPolicyExtension.register(registry, engine, InMemoryRecordVerificationService.withS1Record());

        for (var scope : java.util.List.of(SCOPE_NEGOTIATION, KoreaPolicyConstants.SCOPE_TRANSFER)) {
            assertTrue(registry.isInScope(KR_LEGAL_BASIS, scope));
            assertTrue(registry.isInScope(KR_SAFE_AREA_PROCESSING, scope));
            assertTrue(registry.isInScope(KR_PSEUDONYMIZATION_LEVEL, scope));
            assertTrue(registry.isInScope(KR_REFERENCE_LAW, scope));
            assertTrue(registry.isInScope(ACTION_USE, scope));
            assertTrue(registry.isInScope(ACTION_PSEUDONYMIZE, scope));
            assertTrue(registry.isInScope(ACTION_REIDENTIFY, scope));
        }
    }

    @Test
    void edcPolicyEngineFailsMissingSafeAreaProcessing() {
        var service = new InMemoryRecordVerificationService();
        service.put("missing-safe-area", AuthorizationRecord.s1().withoutSafeAreaProcessing());
        var registry = new RuleBindingRegistryImpl();
        var engine = new PolicyEngineImpl(new ScopeFilter(registry), new RuleValidator(registry));
        KoreaPolicyExtension.register(registry, engine, service);

        var policy = Policy.Builder.newInstance()
                .permission(Permission.Builder.newInstance()
                        .action(action(ACTION_USE))
                        .constraint(constraint(KR_SAFE_AREA_PROCESSING, Operator.EQ, true))
                        .build())
                .build();

        var result = engine.evaluate(policy, context("missing-safe-area"));
        assertTrue(result.failed(), "EDC policy engine should fail when safe-area processing is required but absent.");
    }

    @Test
    void serviceLoaderFindsKoreaPolicyExtension() {
        var found = ServiceLoader.load(ServiceExtension.class).stream()
                .map(ServiceLoader.Provider::type)
                .anyMatch(KoreaPolicyExtension.class::equals);

        assertTrue(found, "KoreaPolicyExtension must be published as an EDC ServiceExtension.");
    }

    @Test
    void policyValidationRecognizesRegisteredOperands() {
        var registry = new RuleBindingRegistryImpl();
        var engine = new PolicyEngineImpl(new ScopeFilter(registry), new RuleValidator(registry));
        KoreaPolicyExtension.register(registry, engine, InMemoryRecordVerificationService.withS1Record());

        var policy = Policy.Builder.newInstance()
                .permission(Permission.Builder.newInstance()
                        .action(action(ACTION_USE))
                        .constraint(constraint(KR_LEGAL_BASIS, Operator.EQ, PIPA_28_2))
                        .build())
                .build();

        assertTrue(engine.validate(policy).succeeded());
        assertEquals(KoreaPolicyContext.class, context("s1-valid").getClass());
    }

    private static KoreaPolicyContext context(String recordId) {
        return new KoreaPolicyContext(SCOPE_NEGOTIATION, recordId);
    }

    private static Permission permission() {
        return Permission.Builder.newInstance().action(action("odrl:use")).build();
    }

    private static Duty duty() {
        return Duty.Builder.newInstance().action(action(ACTION_PSEUDONYMIZE)).build();
    }

    private static Prohibition prohibition() {
        return Prohibition.Builder.newInstance()
                .action(action(ACTION_REIDENTIFY))
                .constraint(constraint(KR_REFERENCE_LAW, Operator.EQ, PIPA_28_5))
                .build();
    }

    private static Action action(String type) {
        return Action.Builder.newInstance().type(type).build();
    }

    private static AtomicConstraint constraint(String left, Operator operator, Object right) {
        return AtomicConstraint.Builder.newInstance()
                .leftExpression(new LiteralExpression(left))
                .operator(operator)
                .rightExpression(new LiteralExpression(right))
                .build();
    }
}
