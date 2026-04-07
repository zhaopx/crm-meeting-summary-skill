# Mock Data Layout

Use mock data to simulate runtime retrieval before real CRM integration.

## Directory layout

- `meeting-records/` - raw meeting input packages
- `crm/customer/` - customer CRM objects
- `crm/opportunity/` - opportunity CRM objects
- `crm/initiator/` - initiator/stakeholder CRM objects
- `memory/initiator/` - initiator memory
- `memory/customer/` - customer memory
- `memory/opportunity/` - opportunity memory

## Key rule
- prefer ID-based files when IDs exist
- fall back to name-based files when IDs are absent
- do not create duplicate truth sources for the same object without documenting precedence

## Suggested extension
When a name-based fallback is needed, use a normalized filename such as:
- `华东零售集团.json`
- `李总.json`

Keep the same object content shape regardless of key style.
