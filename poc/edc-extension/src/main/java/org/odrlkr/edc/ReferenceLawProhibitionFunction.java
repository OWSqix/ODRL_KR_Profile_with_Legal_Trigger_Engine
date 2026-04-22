package org.odrlkr.edc;

import org.eclipse.edc.policy.engine.spi.AtomicConstraintRuleFunction;
import org.eclipse.edc.policy.model.Operator;
import org.eclipse.edc.policy.model.Prohibition;

public final class ReferenceLawProhibitionFunction implements AtomicConstraintRuleFunction<Prohibition, KoreaPolicyContext> {
    private final RecordVerificationService records;

    public ReferenceLawProhibitionFunction(RecordVerificationService records) {
        this.records = records;
    }

    @Override
    public boolean evaluate(Operator operator, Object rightValue, Prohibition rule, KoreaPolicyContext context) {
        if (operator != Operator.EQ) {
            context.reportProblem("ODRL-KR reference-law prohibition supports only EQ, got " + operator);
            return false;
        }
        if (!(rightValue instanceof String referenceLaw)) {
            context.reportProblem("ODRL-KR reference-law rightOperand must be a String.");
            return false;
        }

        var record = records.verify(context.recordId());
        if (!record.active()) {
            context.reportProblem("AuthorizationRecord is not active: " + context.recordId());
            return false;
        }
        if (!record.prohibitionRules().contains(referenceLaw)) {
            context.reportProblem("Reference law " + referenceLaw + " is not present in prohibition rules.");
            return false;
        }
        return true;
    }
}
