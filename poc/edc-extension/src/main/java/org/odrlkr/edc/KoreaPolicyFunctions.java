package org.odrlkr.edc;

/**
 * Pure semantic helpers used by the EDC SPI functions and by focused unit tests.
 */
public final class KoreaPolicyFunctions {
    private KoreaPolicyFunctions() {
    }

    public static boolean legalBasisAllows(AuthorizationRecord record, String rightOperand) {
        return record.active() && record.legalBasis().equals(rightOperand);
    }

    public static boolean pseudonymizationRankAtLeast(AuthorizationRecord record, int requiredRank) {
        return record.active() && record.pseudonymizationRank() >= requiredRank;
    }

    public static boolean safeAreaDutySatisfied(AuthorizationRecord record) {
        return record.active()
                && (!record.safeAreaProcessingRequired() || record.safeAreaProcessingPresent());
    }

    public static boolean actionAllowed(AuthorizationRecord record, String action) {
        if (KoreaPolicyConstants.ACTION_REIDENTIFY.equals(action)
                && record.prohibitionRules().contains(KoreaPolicyConstants.PIPA_28_5)) {
            return false;
        }
        return record.active();
    }
}
