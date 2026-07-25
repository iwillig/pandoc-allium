---
title: All error types in one spec
---

# All error types in one spec

This single `allium check` run produces every diagnostic category:
errors, warnings, and info. It's the canonical example for testing the
full diagnostics display pipeline.

```allium
-- allium: 1

entity Order {
    id: UUID
    status: pending | processing | shipped | delivered
    notes: String
}

entity Customer {
    id: Integer
    name: String
}

rule StartProcessing {
    when: o: Order.status
    requires: o.status = pending
    ensures: o.status = processing
}

rule ShipOrder {
    when: o: Order.status
    requires: o.status = processing
    ensures: o.status = shipped
}
```
