---
title: Multi-entity spec example
---

# Multi-entity spec

A more realistic spec with multiple entities, transitions, and a rule
that references another entity's field.

```allium
-- allium: 1

entity Task {
    id: Integer
    priority: low | medium | high
    assigned_to: Integer
}

entity Worker {
    id: Integer
    available: yes | no
}

rule AssignTask {
    when: t: Task.priority
    requires: t.assigned_to = 0
    ensures: t.priority = high
}

rule CompleteTask {
    when: t: Task.priority
    requires: t.priority = high
    ensures: t.priority = low
}

rule FreeWorker {
    when: w: Worker.available
    requires: w.available = no
    ensures: w.available = yes
}
```
