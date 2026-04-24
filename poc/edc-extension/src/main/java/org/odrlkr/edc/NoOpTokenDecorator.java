package org.odrlkr.edc;

import org.eclipse.edc.spi.iam.TokenParameters;
import org.eclipse.edc.token.spi.TokenDecorator;

/**
 * Leaves DSP token parameters unchanged while satisfying the runtime's TokenDecorator slot.
 */
public final class NoOpTokenDecorator implements TokenDecorator {
    @Override
    public TokenParameters.Builder decorate(TokenParameters.Builder builder) {
        return builder;
    }
}

