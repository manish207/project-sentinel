# TM-013 — Recurring Tasks

**Epic:** Personal Task Management

**Priority:** P0

**Status:** Ready

**Milestone:** Release 0.2

---

# Objective

Allow tasks to automatically repeat according to a defined schedule.

Recurring tasks should generate future task instances without modifying historical records.

---

# Business Value

Users frequently manage recurring work such as:

* Daily stand-ups
* Weekly reports
* Monthly reviews
* Quarterly audits
* Annual renewals

Automation reduces repetitive data entry.

---

# Functional Requirements

Support recurrence patterns:

* Daily
* Weekly
* Monthly
* Yearly
* Weekdays
* Custom interval

Support:

* Start date
* End date
* Maximum occurrences
* Pause recurrence
* Resume recurrence

---

# Domain Changes

Introduce:

RecurringTaskRule

Fields:

* frequency
* interval
* weekdays
* month_day
* start_date
* end_date
* occurrence_limit
* active

Link rules to tasks.

---

# Database

New table:

recurrence_rules

Reference originating task.

Store recurrence metadata separately from task instances.

---

# Services

Responsibilities:

* Generate next occurrence
* Skip completed periods
* Pause and resume schedules
* Preserve task history

---

# CLI

Examples:

```text
project-sentinel task recurrence create TASK_ID --daily
project-sentinel task recurrence create TASK_ID --weekly Monday
project-sentinel task recurrence pause TASK_ID
project-sentinel task recurrence resume TASK_ID
project-sentinel task recurrence delete TASK_ID
```

---

# Future API

Expose recurrence management endpoints.

Support RFC 5545 (iCalendar RRULE) in future versions where practical.

---

# Performance

Generation should be incremental.

Do not pre-create years of future tasks.

---

# Tests

* Daily recurrence
* Weekly recurrence
* Monthly recurrence
* End-date handling
* Occurrence limits
* Pause/resume
* Repository persistence
* CLI commands

---

# Acceptance Criteria

* Recurring schedules generate tasks correctly.
* Historical tasks remain unchanged.
* Future tasks are generated predictably.
* No duplicate task generation.
* Tests pass.
