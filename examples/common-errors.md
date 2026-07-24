---
title: Common Allium errors
---

# Common Allium errors

These examples show typical mistakes and what `allium check` reports.

## Missing version marker

Every spec file must start with `-- allium: 1` (or the version you target).

```allium
entity Light {
    id: Integer
    state: on | off
}
```

## Undefined type reference

All types must be declared locally or imported — `UUID` is not a built-in.

```allium
-- allium: 1

entity Invoice {
    id: UUID
    amount: Decimal
}
```

## Unused entity

An entity not referenced by any rule or other entity triggers a warning.

```allium
-- allium: 1

entity Server {
    id: Integer
    status: running | stopped
}

rule Restart {
    when: s: Server.status
    requires: s.status = stopped
    ensures: s.status = running
}

entity Database {
    id: Integer
    connected: yes | no
}
```

## Status with no exit transition

A status that nothing transitions *out of* is flagged.

```allium
-- allium: 1

entity Deployment {
    id: Integer
    phase: pending | building | deployed
}

rule StartBuild {
    when: d: Deployment.phase
    requires: d.phase = pending
    ensures: d.phase = building
}

rule FinishBuild {
    when: d: Deployment.phase
    requires: d.phase = building
    ensures: d.phase = deployed
}
```

## Intentionally broken (skipped)

This block uses `.no-check` so it's left as-is — useful for docs that
want to show a mistake without the checker running on it.

```{.allium .no-check}
-- allium: 1
entity Broken {
    field: NotARealType
}
```
