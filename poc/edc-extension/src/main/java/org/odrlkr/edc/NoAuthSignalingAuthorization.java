package org.odrlkr.edc;

import org.eclipse.edc.connector.dataplane.selector.spi.instance.AuthorizationProfile;
import org.eclipse.edc.signaling.spi.authorization.Header;
import org.eclipse.edc.signaling.spi.authorization.SignalingAuthorization;
import org.eclipse.edc.spi.result.Result;

import java.util.function.Function;

/**
 * Minimal signaling authorization profile used only for local PoC runtimes.
 */
public final class NoAuthSignalingAuthorization implements SignalingAuthorization {
    public static final String TYPE = "none";

    @Override
    public String getType() {
        return TYPE;
    }

    @Override
    public Result<String> isAuthorized(Function<String, String> headerSupplier) {
        return Result.success("");
    }

    @Override
    public Result<Header> evaluate(AuthorizationProfile authorizationProfile) {
        return Result.success(new Header("X-ODRLKR-NoAuth", "1"));
    }
}
