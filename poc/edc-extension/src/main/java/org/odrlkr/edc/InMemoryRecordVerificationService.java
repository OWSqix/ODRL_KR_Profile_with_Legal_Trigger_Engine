package org.odrlkr.edc;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public final class InMemoryRecordVerificationService implements RecordVerificationService {
    private final Map<String, AuthorizationRecord> records = new ConcurrentHashMap<>();

    public static InMemoryRecordVerificationService withS1Record() {
        var service = new InMemoryRecordVerificationService();
        service.put("s1-valid", AuthorizationRecord.s1());
        return service;
    }

    public void put(String recordId, AuthorizationRecord record) {
        records.put(recordId, record);
    }

    @Override
    public AuthorizationRecord verify(String recordId) {
        var record = records.get(recordId);
        if (record == null) {
            return AuthorizationRecord.inactive();
        }
        return record;
    }
}
