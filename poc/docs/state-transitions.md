# AuthorizationRecord State Transitions

LegalBasisRecord and ConsentReceipt share the AuthorizationRecord abstraction, but their state semantics differ.

| Record type | Allowed terminal/admin states | Meaning |
| --- | --- | --- |
| ConsentReceipt | `expired`, `revoked` | Consent can expire or be revoked by the consent flow. |
| LegalBasisRecord | `expired`, `invalidated`, `superseded` | A legal-basis record can expire, be invalidated by issuer/governance, or be replaced by a newer record. |

For S1, the valid record is `active`. Because it is a PIPA Section 28-2 pseudonymized-data legal-basis flow, `transferRight.applicable` is `false` with `kr:PIPA-28-7` as the exclusion basis.
