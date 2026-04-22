package org.odrlkr.edc;

public final class KoreaPolicyConstants {
    public static final String SCOPE_NEGOTIATION = "contract.negotiation";
    public static final String SCOPE_TRANSFER = "transfer.process";

    public static final String KR_LEGAL_BASIS = "https://w3id.org/odrl-kr#legalBasisOperand";
    public static final String KR_PSEUDONYMIZATION_LEVEL = "https://w3id.org/odrl-kr#pseudonymizationLevel";
    public static final String KR_SAFE_AREA_PROCESSING = "https://w3id.org/odrl-kr#safeAreaProcessing";
    public static final String KR_REFERENCE_LAW = "https://w3id.org/odrl-kr#referenceLaw";

    public static final String ACTION_USE = "odrl:use";
    public static final String ACTION_PSEUDONYMIZE = "kr:pseudonymize";
    public static final String ACTION_REIDENTIFY = "kr:re-identify";

    public static final String PIPA_28_2 = "kr:PIPA-28-2";
    public static final String PIPA_28_5 = "kr:PIPA-28-5";
    public static final String PSEUDONYMIZATION_LEVEL_1 = "kr:Pseudonymization-Level-1";
    public static final String PSEUDONYMIZATION_LEVEL_2 = "kr:Pseudonymization-Level-2";
    public static final String PSEUDONYMIZATION_LEVEL_3 = "kr:Pseudonymization-Level-3";

    private KoreaPolicyConstants() {
    }
}
