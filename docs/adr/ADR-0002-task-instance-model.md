# ADR-0002 — Separate Task Template and Task Instance

**Status:** Accepted

**Date:** 2026-07-07

---

# Context

Project Sentinel will support:

* One-time tasks
* Recurring tasks
* AI scheduling
* Calendar synchronization
* Notifications
* History
* Analytics

A recurring task creates multiple occurrences over time.

If recurrence information is stored directly inside a task, the same object represents both:

* the recurring definition
* the completed occurrence

This leads to increasingly complex business rules.

---

# Decision

Project Sentinel will distinguish between:

## Task Template

Represents the definition of work.

Contains:

* title
* description
* recurrence rule
* default priority
* estimated duration
* tags
* project
* workspace

A Task Template does **not** represent work that has already happened.

---

## Task Instance

Represents one occurrence generated from a Task Template.

Contains:

* scheduled date
* due date
* completion date
* status
* actual duration
* notes
* attachments
* comments

Every instance references exactly one Task Template.

One template may produce zero, one, or many instances.

---

# Why

This separation simplifies:

* recurring tasks
* calendar synchronization
* AI scheduling
* reminders
* reporting
* analytics
* historical tracking

It also avoids modifying completed tasks when recurrence rules change.

---

# Example

Daily Standup

Template

↓

2026-07-07 ✅

↓

2026-07-08 ⏳

↓

2026-07-09 ⏳

Changing the template affects future instances only.

Completed instances remain unchanged.

---

# Benefits

* Cleaner domain model
* Better historical accuracy
* Easier synchronization
* Better AI planning
* Better reporting
* Supports future calendar integrations

---

# Trade-offs

Additional tables.

Additional repositories.

Slightly more complex services.

These costs are outweighed by improved scalability and maintainability.

---

# Consequences

Future work should treat Task Templates and Task Instances as distinct concepts.

Features such as recurrence, reminders, calendar synchronization, analytics, and AI scheduling should operate using this separation.
