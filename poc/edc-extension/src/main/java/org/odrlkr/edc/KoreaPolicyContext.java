package org.odrlkr.edc;

import org.eclipse.edc.policy.engine.spi.PolicyContextImpl;

public final class KoreaPolicyContext extends PolicyContextImpl {
    private final String scope;
    private final String recordId;

    public KoreaPolicyContext(String scope, String recordId) {
        this.scope = scope;
        this.recordId = recordId;
    }

    @Override
    public String scope() {
        return scope;
    }

    public String recordId() {
        return recordId;
    }
}
