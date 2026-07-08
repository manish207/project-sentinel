# TM-012 — Task Dependencies

**Epic:** Personal Task Management

**Priority:** P0

**Status:** Ready

**Milestone:** Release 0.2

---

# Objective

Allow tasks to depend on other tasks so work can be planned and executed in the correct order.

Dependencies should support planning, scheduling, and future AI recommendations.

---

# Business Value

Many real-world tasks cannot begin until another task has been completed.

Examples:

* Deploy application after testing
* Submit report after approval
* Review code after implementation

Dependencies enable intelligent planning.

---

# Functional Requirements

A task may depend on zero or more tasks.

A task may have zero or more dependent tasks.

Support multiple dependencies.

Support dependency visualization.

---

# Domain Changes

Create a dependency model.

Fields:

* id
* predecessor_task_id
* successor_task_id
* dependency_type

Supported dependency types:

* Finish-to-Start (default)
* Start-to-Start
* Finish-to-Finish
* Start-to-Finish (reserved for future)

---

# Validation

Reject:

* Circular dependencies
* Self-dependencies
* Duplicate dependencies
* Missing task references

---

# Database

Create a task_dependencies table.

Indexes:

* predecessor_task_id
* successor_task_id

Cascade delete should remove only dependency records, never tasks.

---

# Repository

Support:

* add_dependency()
* remove_dependency()
* get_dependencies()
* get_dependents()
* dependency_graph()

---

# Services

Business rules:

* Prevent completion if blocking dependencies are incomplete (configurable).
* Expose dependency graph.
* Calculate "ready to start" tasks.

---

# CLI

New commands:

```text
project-sentinel task dependency add TASK_A TASK_B
project-sentinel task dependency remove TASK_A TASK_B
project-sentinel task dependency list TASK_ID
project-sentinel task dependency graph
```

---

# Future API

Provide REST endpoints for dependency management.

---

# Performance

Optimize graph traversal for large task sets.

Avoid N+1 queries.

---

# Tests

* Dependency creation
* Circular dependency rejection
* Duplicate rejection
* Repository graph queries
* CLI integration
* Service validation

---

# Acceptance Criteria

* Dependencies persist correctly.
* Invalid graphs are rejected.
* Ready-to-start tasks are calculated correctly.
* Existing task behavior remains unchanged.
* All tests pass.
