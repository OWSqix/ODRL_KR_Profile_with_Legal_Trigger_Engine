package org.odrlkr.edc;

import java.util.List;

public record AuthorizationRecord(
        boolean active,
        String legalBasis,
        int pseudonymizationRank,
        boolean safeAreaProcessingRequired,
        boolean safeAreaProcessingPresent,
        List<String> prohibitionRules) {

    public static AuthorizationRecord s1() {
        return new AuthorizationRecord(
                true,
                KoreaPolicyConstants.PIPA_28_2,
                2,
                true,
                true,
                List.of(KoreaPolicyConstants.PIPA_28_5));
    }

    public static AuthorizationRecord inactive() {
        return new AuthorizationRecord(
                false,
                "",
                0,
                false,
                false,
                List.of());
    }

    public AuthorizationRecord withLegalBasis(String value) {
        return new AuthorizationRecord(
                active,
                value,
                pseudonymizationRank,
                safeAreaProcessingRequired,
                safeAreaProcessingPresent,
                prohibitionRules);
    }

    public AuthorizationRecord withPseudonymizationRank(int rank) {
        return new AuthorizationRecord(
                active,
                legalBasis,
                rank,
                safeAreaProcessingRequired,
                safeAreaProcessingPresent,
                prohibitionRules);
    }

    public AuthorizationRecord withoutSafeAreaProcessing() {
        return new AuthorizationRecord(
                active,
                legalBasis,
                pseudonymizationRank,
                safeAreaProcessingRequired,
                false,
                prohibitionRules);
    }
}
