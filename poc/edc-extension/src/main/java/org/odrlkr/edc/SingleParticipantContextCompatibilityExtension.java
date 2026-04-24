package org.odrlkr.edc;

import org.eclipse.edc.participantcontext.single.spi.SingleParticipantContextSupplier;
import org.eclipse.edc.participantcontext.spi.config.model.ParticipantContextConfiguration;
import org.eclipse.edc.participantcontext.spi.config.store.ParticipantContextConfigStore;
import org.eclipse.edc.participantcontext.spi.identity.ParticipantIdentityResolver;
import org.eclipse.edc.participantcontext.spi.types.ParticipantContext;
import org.eclipse.edc.participantcontext.spi.types.ParticipantContextState;
import org.eclipse.edc.runtime.metamodel.annotation.Extension;
import org.eclipse.edc.runtime.metamodel.annotation.Inject;
import org.eclipse.edc.runtime.metamodel.annotation.Provider;
import org.eclipse.edc.spi.result.ServiceResult;
import org.eclipse.edc.spi.system.ServiceExtension;
import org.eclipse.edc.spi.system.ServiceExtensionContext;

/**
 * Supplies the single-participant context service expected by EDC 0.17.0 API extensions.
 *
 * <p>The 0.17.0 connector modules still inject {@code SingleParticipantContextSupplier},
 * but this PoC assembles a minimal local runtime from discrete Maven modules rather than
 * a prebuilt distribution. This compatibility extension provides the single active context
 * derived from the runtime's participant settings so the DSP smoke test can boot.
 */
@Extension("ODRL-KR Single Participant Context Compatibility")
public final class SingleParticipantContextCompatibilityExtension implements ServiceExtension {
    @Inject(required = false)
    private ParticipantContextConfigStore configStore;

    private ParticipantContext participantContext;

    @Override
    public void initialize(ServiceExtensionContext context) {
        var participantId = context.getSetting("edc.participant.id", "anonymous");
        var configuredContextId = context.getSetting("edc.participant.context.id", participantId);

        participantContext = ParticipantContext.Builder.newInstance()
                .participantContextId(configuredContextId)
                .identity(participantId)
                .state(ParticipantContextState.ACTIVATED)
                .build();

        if (configStore != null) {
            var configuration = ParticipantContextConfiguration.Builder.newInstance()
                    .participantContextId(configuredContextId)
                    .entry("edc.participant.id", participantId)
                    .entry("edc.mock.region", context.getSetting("edc.mock.region", "eu"))
                    .entry("edc.mock.faulty_client_id", context.getSetting("edc.mock.faulty_client_id", "faultyClientId"))
                    .build();
            configStore.save(configuration);
        }
    }

    @Provider
    public SingleParticipantContextSupplier singleParticipantContextSupplier() {
        return () -> ServiceResult.success(participantContext);
    }

    @Provider
    public ParticipantIdentityResolver participantIdentityResolver() {
        return (participantContextId, defaultParticipantId) -> participantContext.getIdentity();
    }
}
