---
title: Workflow state machine
---

# Workflow state machine

A complete workflow with entry, intermediate, and terminal states.
`allium check` will still surface info-level diagnostics (unused fields)
but no errors.

```allium
-- allium: 1

entity PullRequest {
    id: Integer
    state: draft | review | approved | merged | closed
    author: Integer
}

rule SubmitForReview {
    when: pr: PullRequest.state
    requires: pr.state = draft
    ensures: pr.state = review
}

rule Approve {
    when: pr: PullRequest.state
    requires: pr.state = review
    ensures: pr.state = approved
}

rule RequestChanges {
    when: pr: PullRequest.state
    requires: pr.state = review
    ensures: pr.state = draft
}

rule Merge {
    when: pr: PullRequest.state
    requires: pr.state = approved
    ensures: pr.state = merged
}

rule Close {
    when: pr: PullRequest.state
    requires: pr.state = draft
    ensures: pr.state = closed
}
```
