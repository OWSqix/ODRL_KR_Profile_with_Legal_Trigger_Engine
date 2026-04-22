package org.odrlkr.edc;

import org.eclipse.edc.policy.engine.spi.AtomicConstraintRuleFunction;
import org.eclipse.edc.policy.model.Operator;
import org.eclipse.edc.policy.model.Permission;

public final class LegalBasisPermissionFunction implements AtomicConstraintRuleFunction<Permission, KoreaPolicyContext> {
    private final RecordVerificationService records;

    public LegalBasisPermissionFunction(RecordVerificationService records) {
        this.records = records;
    }

    @Override
    public boolean evaluate(Operator operator, Object rightValue, Permission rule, KoreaPolicyContext context) {
        if (operator != Operator.EQ) {
            context.reportProblem("ODRL-KR legal basis supports only EQ, got " + operator);
            return false;
        }
        if (!(rightValue instanceof String expectedBasis)) {
            context.reportProblem("ODRL-KR legal basis rightOperand must be a String.");
            return false;
        }

        var record = records.verify(context.recordId());
        if (!record.active()) {
            context.reportProblem("AuthorizationRecord is not active: " + context.recordId());
            return false;
        }
        if (!expectedBasis.equals(record.legalBasis())) {
            context.reportProblem("Legal basis mismatch: expected " + expectedBasis + " but was " + record.legalBasis());
            return false;
        }
        return true;
    }
}
