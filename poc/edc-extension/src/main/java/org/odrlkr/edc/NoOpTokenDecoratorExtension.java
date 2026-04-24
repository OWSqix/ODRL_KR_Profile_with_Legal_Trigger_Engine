package org.odrlkr.edc;

import org.eclipse.edc.runtime.metamodel.annotation.Extension;
import org.eclipse.edc.runtime.metamodel.annotation.Provider;
import org.eclipse.edc.spi.system.ServiceExtension;
import org.eclipse.edc.token.spi.TokenDecorator;

@Extension("ODRL-KR No-Op Token Decorator")
public final class NoOpTokenDecoratorExtension implements ServiceExtension {
    @Provider
    public TokenDecorator tokenDecorator() {
        return new NoOpTokenDecorator();
    }
}
