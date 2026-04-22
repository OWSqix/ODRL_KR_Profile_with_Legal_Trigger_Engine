package org.odrlkr.edc;

import org.eclipse.edc.connector.dataplane.spi.Endpoint;
import org.eclipse.edc.connector.dataplane.spi.iam.DataPlaneAuthorizationService;
import org.eclipse.edc.connector.dataplane.spi.iam.PublicEndpointGeneratorService;
import org.eclipse.edc.policy.engine.spi.PolicyEngine;
import org.eclipse.edc.policy.engine.spi.RuleBindingRegistry;
import org.eclipse.edc.policy.model.Duty;
import org.eclipse.edc.policy.model.Permission;
import org.eclipse.edc.policy.model.Prohibition;
import org.eclipse.edc.runtime.metamodel.annotation.Extension;
import org.eclipse.edc.runtime.metamodel.annotation.Inject;
import org.eclipse.edc.spi.system.ServiceExtension;
import org.eclipse.edc.spi.system.ServiceExtensionContext;
import org.eclipse.edc.spi.security.Vault;
import org.eclipse.edc.transform.spi.TypeTransformerRegistry;

import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.Map;

import static org.odrlkr.edc.KoreaPolicyConstants.ACTION_PSEUDONYMIZE;
import static org.odrlkr.edc.KoreaPolicyConstants.ACTION_REIDENTIFY;
import static org.odrlkr.edc.KoreaPolicyConstants.ACTION_USE;
import static org.odrlkr.edc.KoreaPolicyConstants.KR_LEGAL_BASIS;
import static org.odrlkr.edc.KoreaPolicyConstants.KR_PSEUDONYMIZATION_LEVEL;
import static org.odrlkr.edc.KoreaPolicyConstants.KR_REFERENCE_LAW;
import static org.odrlkr.edc.KoreaPolicyConstants.KR_SAFE_AREA_PROCESSING;
import static org.odrlkr.edc.KoreaPolicyConstants.SCOPE_NEGOTIATION;
import static org.odrlkr.edc.KoreaPolicyConstants.SCOPE_TRANSFER;

/**
 * EDC 0.16.0 policy extension for the ODRL-KR proof background.
 *
 * <p>This class compiles against EDC 0.16.0 policy-engine SPI and registers
 * concrete policy functions for the proof scenario.
 */
@Extension("ODRL-KR Policy Extension")
public final class KoreaPolicyExtension implements ServiceExtension {
    @Inject
    private RuleBindingRegistry bindings;

    @Inject
    private PolicyEngine engine;

    @Inject(required = false)
    private RecordVerificationService records;

    @Inject(required = false)
    private TypeTransformerRegistry transformerRegistry;

    @Inject(required = false)
    private PublicEndpointGeneratorService publicEndpointGenerator;

    @Inject(required = false)
    private DataPlaneAuthorizationService dataPlaneAuthorizationService;

    @Inject(required = false)
    private Vault vault;

    private HttpServer publicPayloadServer;

    @Override
    public void initialize(ServiceExtensionContext context) {
        if (transformerRegistry != null) {
            transformerRegistry.register(new JsonValueToObjectTransformer());
        }
        if (vault != null) {
            var privateKey = context.getSetting("private-key", null);
            var publicKey = context.getSetting("public-key", null);
            if (privateKey != null && !privateKey.isBlank()) {
                vault.storeSecret("private-key", privateKey.replace("\\n", "\n"));
            }
            if (publicKey != null && !publicKey.isBlank()) {
                vault.storeSecret("public-key", publicKey.replace("\\n", "\n"));
            }
        }
        if (publicEndpointGenerator != null) {
            var publicBaseUrl = context.getSetting("edc.dataplane.api.public.baseurl", "http://localhost:19291/public");
            publicEndpointGenerator.addGeneratorFunction("HttpData", ignored -> Endpoint.url(publicBaseUrl));
            if (dataPlaneAuthorizationService != null) {
                startPublicPayloadEndpoint(publicBaseUrl);
            }
        }
        register(bindings, engine, records != null ? records : InMemoryRecordVerificationService.withS1Record());
    }

    @Override
    public void shutdown() {
        if (publicPayloadServer != null) {
            publicPayloadServer.stop(0);
            publicPayloadServer = null;
        }
    }

    public static void register(RuleBindingRegistry bindings, PolicyEngine engine, RecordVerificationService records) {
        engine.registerScope(SCOPE_NEGOTIATION, KoreaPolicyContext.class);
        engine.registerScope(SCOPE_TRANSFER, KoreaPolicyContext.class);

        bindForRuntimeScopes(bindings, KR_LEGAL_BASIS);
        bindForRuntimeScopes(bindings, KR_PSEUDONYMIZATION_LEVEL);
        bindForRuntimeScopes(bindings, KR_SAFE_AREA_PROCESSING);
        bindForRuntimeScopes(bindings, KR_REFERENCE_LAW);
        bindForRuntimeScopes(bindings, ACTION_USE);
        bindForRuntimeScopes(bindings, ACTION_PSEUDONYMIZE);
        bindForRuntimeScopes(bindings, ACTION_REIDENTIFY);

        engine.registerFunction(KoreaPolicyContext.class, Permission.class, KR_LEGAL_BASIS,
                new LegalBasisPermissionFunction(records));
        engine.registerFunction(KoreaPolicyContext.class, Permission.class, KR_SAFE_AREA_PROCESSING,
                new SafeAreaPermissionFunction(records));
        engine.registerFunction(KoreaPolicyContext.class, Duty.class, KR_PSEUDONYMIZATION_LEVEL,
                new PseudonymizationDutyFunction(records));
        engine.registerFunction(KoreaPolicyContext.class, Prohibition.class, KR_REFERENCE_LAW,
                new ReferenceLawProhibitionFunction(records));
    }

    private static void bindForRuntimeScopes(RuleBindingRegistry bindings, String leftOperand) {
        bindings.bind(leftOperand, SCOPE_NEGOTIATION);
        bindings.bind(leftOperand, SCOPE_TRANSFER);
    }

    private void startPublicPayloadEndpoint(String publicBaseUrl) {
        try {
            var uri = URI.create(publicBaseUrl);
            var port = uri.getPort();
            if (port < 0) {
                return;
            }
            var path = uri.getPath() == null || uri.getPath().isBlank() ? "/" : uri.getPath();
            var client = HttpClient.newHttpClient();
            publicPayloadServer = HttpServer.create(new InetSocketAddress("localhost", port), 0);
            publicPayloadServer.createContext(path, exchange -> {
                var token = exchange.getRequestHeaders().getFirst("Authorization");
                if (token == null || token.isBlank()) {
                    writeResponse(exchange, 401, "Missing Authorization token.");
                    return;
                }
                var authorized = dataPlaneAuthorizationService.authorize(token, Map.of(
                        "path", exchange.getRequestURI().getPath(),
                        "method", exchange.getRequestMethod()
                ));
                if (authorized.failed()) {
                    writeResponse(exchange, 403, authorized.getFailureDetail());
                    return;
                }
                var source = authorized.getContent();
                var sourceUrl = source.getStringProperty("baseUrl");
                if (sourceUrl == null || sourceUrl.isBlank()) {
                    writeResponse(exchange, 502, "Authorized source DataAddress has no baseUrl.");
                    return;
                }
                try {
                    var upstreamRequest = HttpRequest.newBuilder(URI.create(sourceUrl)).GET().build();
                    var upstreamResponse = client.send(upstreamRequest, HttpResponse.BodyHandlers.ofByteArray());
                    exchange.getResponseHeaders().add("content-type",
                            upstreamResponse.headers().firstValue("content-type").orElse("application/octet-stream"));
                    exchange.sendResponseHeaders(upstreamResponse.statusCode(), upstreamResponse.body().length);
                    try (var body = exchange.getResponseBody()) {
                        body.write(upstreamResponse.body());
                    }
                } catch (InterruptedException exception) {
                    Thread.currentThread().interrupt();
                    writeResponse(exchange, 500, exception.getMessage());
                } catch (IOException | IllegalArgumentException exception) {
                    writeResponse(exchange, 502, exception.getMessage());
                }
            });
            publicPayloadServer.start();
        } catch (IllegalArgumentException | IOException ignored) {
            // Local authenticated public endpoint for connector-level E2E tests.
            // If it cannot bind, normal EDC boot should continue and tests will expose the failure.
        }
    }

    private void writeResponse(com.sun.net.httpserver.HttpExchange exchange, int status, String message) throws IOException {
        var bytes = message.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().add("content-type", "text/plain; charset=utf-8");
        exchange.sendResponseHeaders(status, bytes.length);
        try (var body = exchange.getResponseBody()) {
            body.write(bytes);
        }
    }
}
