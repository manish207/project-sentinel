# TM-011 — Subtasks

**Epic:** Personal Task Management

**Priority:** P0

**Status:** Ready

**Milestone:** Release 0.2

---

# Objective

Allow any task to contain child tasks.

Subtasks should behave exactly like normal tasks while remaining linked to their parent.

---

# Business Value

Large tasks become manageable.

Users can progressively complete work while maintaining a clean hierarchy.

---

# Functional Requirements

A task may have zero or more child tasks.

A subtask belongs to exactly one parent.

A parent task may itself be a subtask.

Hierarchy depth is unlimited.

---

# Domain Changes

Task

Add

parent_task_id

children

helper methods

```
add_subtask()

remove_subtask()

has_children()

is_root()
```

---

# Database

Foreign key

parent_task_id

Self-reference

Cascade behavior:

Deleting a parent must not automatically delete children.

Children become root tasks unless explicitly requested.

---

# Repository

Support

get_children()

get_parent()

tree()

---

# Services

Create subtask

Move subtask

Detach subtask

Promote subtask

---

# CLI

task create

Add

--parent

Examples

project-sentinel task create "Write API"

project-sentinel task create "Authentication" --parent TASK_ID

task tree

Display hierarchy.

---

# Validation

Prevent circular references.

Prevent parent=self.

Prevent invalid hierarchy.

---

# Tests

Domain

Repository

Services

CLI

Integration

---

# Acceptance Criteria

* Child tasks are linked correctly.
* Tree traversal works.
* Circular references are rejected.
* Existing commands continue working.
* Tests pass.
* Documentation updated.

---

# Definition of Done

* Feature implemented.
* Tests added.
* CI passes.
* No regressions.
