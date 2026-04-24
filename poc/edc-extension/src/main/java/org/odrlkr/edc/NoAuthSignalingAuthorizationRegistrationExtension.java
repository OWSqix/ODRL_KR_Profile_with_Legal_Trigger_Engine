package org.odrlkr.edc;

import org.eclipse.edc.runtime.metamodel.annotation.Extension;
import org.eclipse.edc.runtime.metamodel.annotation.Inject;
import org.eclipse.edc.signaling.spi.authorization.SignalingAuthorizationRegistry;
import org.eclipse.edc.spi.system.ServiceExtension;
import org.eclipse.edc.spi.system.ServiceExtensionContext;

/**
 * Registers the local no-auth signaling profile after the signaling registry exists.
 */
@Extension("ODRL-KR No-Auth Signaling Authorization Registration")
public final class NoAuthSignalingAuthorizationRegistrationExtension implements ServiceExtension {
    @Inject(required = false)
    private SignalingAuthorizationRegistry signalingAuthorizationRegistry;

    @Override
    public void initialize(ServiceExtensionContext context) {
        if (signalingAuthorizationRegistry != null) {
            signalingAuthorizationRegistry.register(new NoAuthSignalingAuthorization());
        }
    }
}
