package org.odrlkr.edc;

import org.eclipse.edc.policy.engine.spi.AtomicConstraintRuleFunction;
import org.eclipse.edc.policy.model.Operator;
import org.eclipse.edc.policy.model.Permission;

public final class SafeAreaPermissionFunction implements AtomicConstraintRuleFunction<Permission, KoreaPolicyContext> {
    private final RecordVerificationService records;

    public SafeAreaPermissionFunction(RecordVerificationService records) {
        this.records = records;
    }

    @Override
    public boolean evaluate(Operator operator, Object rightValue, Permission rule, KoreaPolicyContext context) {
        if (operator != Operator.EQ) {
            context.reportProblem("ODRL-KR safe-area processing supports only EQ, got " + operator);
            return false;
        }
        if (!(rightValue instanceof Boolean required)) {
            context.reportProblem("ODRL-KR safe-area rightOperand must be Boolean.");
            return false;
        }

        var record = records.verify(context.recordId());
        if (!record.active()) {
            context.reportProblem("AuthorizationRecord is not active: " + context.recordId());
            return false;
        }
        if (required && !record.safeAreaProcessingPresent()) {
            context.reportProblem("Safe-area processing is required but missing.");
            return false;
        }
        return true;
    }
}
