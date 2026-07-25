---
title: pandoc-allium demo
---

# pandoc-allium demo

This file exercises `pandoc-allium` end to end. Build it with:

```sh
pipenv run pandoc -F pandoc-allium \
  --syntax-definition pandoc_allium/syntax/allium.xml \
  --css "$(pipenv run pandoc-allium --css-path)" \
  -s examples/demo.md -o /tmp/demo.html
```

## A clean-ish spec

`allium check` still surfaces warnings/info on a structurally valid spec
(unused fields, statuses with no exit transition, ...) -- the filter
reports every diagnostic it's given, it doesn't filter by severity.

```allium
-- allium: 1

entity Widget {
    id: Integer
    status: idle | active
}

rule Activate {
    when: w: Widget.status
    requires: w.status = idle
    ensures: w.status = active
}
```

## A spec with a real error

```allium
entity Order {
    id: UUID
}
```

## Opting out of checking

Add `.no-check` to keep an intentionally-broken snippet in a doc (e.g. to
illustrate a mistake) without `allium check` running on it at all:

```{.allium .no-check}
this isn't valid allium and that's the point
```
