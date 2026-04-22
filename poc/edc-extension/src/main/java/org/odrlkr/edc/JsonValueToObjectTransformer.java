package org.odrlkr.edc;

import jakarta.json.JsonArray;
import jakarta.json.JsonNumber;
import jakarta.json.JsonObject;
import jakarta.json.JsonString;
import jakarta.json.JsonValue;
import org.eclipse.edc.transform.spi.TransformerContext;
import org.eclipse.edc.transform.spi.TypeTransformer;

import java.util.LinkedHashMap;
import java.util.Map;

public final class JsonValueToObjectTransformer implements TypeTransformer<JsonValue, Object> {
    @Override
    public Class<JsonValue> getInputType() {
        return JsonValue.class;
    }

    @Override
    public Class<Object> getOutputType() {
        return Object.class;
    }

    @Override
    public Object transform(JsonValue input, TransformerContext context) {
        if (input == null || input == JsonValue.NULL) {
            return null;
        }
        if (input instanceof JsonString string) {
            return string.getString();
        }
        if (input instanceof JsonNumber number) {
            if (number.isIntegral()) {
                return number.longValue();
            }
            return number.doubleValue();
        }
        if (input == JsonValue.TRUE) {
            return Boolean.TRUE;
        }
        if (input == JsonValue.FALSE) {
            return Boolean.FALSE;
        }
        if (input instanceof JsonArray array) {
            return array.stream().map(value -> transform(value, context)).toList();
        }
        if (input instanceof JsonObject object) {
            if (object.containsKey("@value")) {
                return transform(object.get("@value"), context);
            }
            Map<String, Object> values = new LinkedHashMap<>();
            object.forEach((key, value) -> values.put(key, transform(value, context)));
            return values;
        }
        context.reportProblem("Unsupported JSON value type for generic object conversion: " + input.getValueType());
        return null;
    }
}
