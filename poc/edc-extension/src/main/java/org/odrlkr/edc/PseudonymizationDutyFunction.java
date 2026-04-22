package org.odrlkr.edc;

import org.eclipse.edc.policy.engine.spi.AtomicConstraintRuleFunction;
import org.eclipse.edc.policy.model.Duty;
import org.eclipse.edc.policy.model.Operator;

import java.util.Map;

public final class PseudonymizationDutyFunction implements AtomicConstraintRuleFunction<Duty, KoreaPolicyContext> {
    private static final Map<String, Integer> RANKS = Map.of(
            KoreaPolicyConstants.PSEUDONYMIZATION_LEVEL_1, 1,
            KoreaPolicyConstants.PSEUDONYMIZATION_LEVEL_2, 2,
            KoreaPolicyConstants.PSEUDONYMIZATION_LEVEL_3, 3);

    private final RecordVerificationService records;

    public PseudonymizationDutyFunction(RecordVerificationService records) {
        this.records = records;
    }

    @Override
    public boolean evaluate(Operator operator, Object rightValue, Duty rule, KoreaPolicyContext context) {
        if (operator != Operator.GEQ) {
            context.reportProblem("ODRL-KR pseudonymization level supports only GEQ, got " + operator);
            return false;
        }

        var requiredRank = rankOf(rightValue);
        if (requiredRank < 0) {
            context.reportProblem("Unknown pseudonymization level rightOperand: " + rightValue);
            return false;
        }

        var record = records.verify(context.recordId());
        if (!record.active()) {
            context.reportProblem("AuthorizationRecord is not active: " + context.recordId());
            return false;
        }
        if (record.pseudonymizationRank() < requiredRank) {
            context.reportProblem("Pseudonymization rank " + record.pseudonymizationRank()
                    + " is lower than required rank " + requiredRank);
            return false;
        }
        return true;
    }

    private int rankOf(Object rightValue) {
        if (rightValue instanceof Number number) {
            return number.intValue();
        }
        if (rightValue instanceof String value) {
            return RANKS.getOrDefault(value, -1);
        }
        return -1;
    }
}
