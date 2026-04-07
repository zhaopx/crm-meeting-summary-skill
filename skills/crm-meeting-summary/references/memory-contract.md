# Memory Contract

Treat memory as an external data source. This skill only reads memory; it does not define how the memory system is produced or governed.

## Memory object scopes
- person
- account
- opportunity
- contact

## CRM object relationship reminder
- account / opportunity / contact can each have an owner
- owner is always a `person`
- a sales record can be initiated under account, opportunity, or contact
- one sales record may link to multiple objects at once
- the initiator is a `person`

## Lookup priority
1. object ID
2. object name
3. ambiguous match -> do not guess, return ambiguity

## Key strategy
Use mixed keys in mock and runtime contracts:
- prefer `*_id` when present
- fall back to `*_name` when ID is absent

## Skill-side usage rules
1. Current meeting record has highest priority.
2. Current CRM data has second priority.
3. Memory is supplemental context only and must not overwrite current evidence.
4. If a memory system provides more fields than needed, read only the minimum relevant subset.

## Suitable skill-side memory usage
- relationship continuity
- stakeholder preference patterns
- prior commitment history
- historical sensitivity or escalation context
- recurring objections or approval patterns

## Unsuitable skill-side memory usage
- do not treat old memory as current fact
- do not infer missing CRM fields from memory alone
- do not use memory to inflate confidence without source support

## Conflict handling
If memory conflicts with current evidence:
1. trust current meeting/CRM evidence
2. note the conflict for review
3. lower confidence if the conflict affects key judgment

## Suggested machine-readable trace

```json
{
  "memory_sources": [
    {
      "scope": "account",
      "lookup_key": "account_id:CUST-001",
      "used": true,
      "notes": ["Provided historical procurement preference context."]
    }
  ],
  "memory_conflicts": []
}
```
