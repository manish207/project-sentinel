# Project Sentinel Product Backlog

Version: 1.0

---

# Purpose

This document is the master implementation backlog for Project Sentinel.

Every feature should originate from this backlog before implementation.

Items are prioritized using the following scale:

* P0 – Critical (must be completed immediately)
* P1 – High
* P2 – Medium
* P3 – Low

Status values:

* Planned
* Ready
* In Progress
* Review
* Testing
* Done

---

# EPIC 1 – Personal Task Management (P0)

**Goal:** Deliver a production-quality local task manager suitable for daily use.

## Core Tasks

| ID     | Feature         | Priority | Status |
| ------ | --------------- | -------- | ------ |
| TM-001 | Workspace CRUD  | Done     | Done   |
| TM-002 | Project CRUD    | Done     | Done   |
| TM-003 | Task CRUD       | Done     | Done   |
| TM-004 | Task Search     | Done     | Done   |
| TM-005 | Task Filtering  | Done     | Done   |
| TM-006 | Task Sorting    | Done     | Done   |
| TM-007 | Task Validation | Done     | Done   |
| TM-008 | Due Dates       | Done     | Done   |
| TM-009 | Tags            | Done     | Done   |
| TM-010 | Priority        | Done     | Done   |

---

## Remaining High-Priority Features

| ID     | Feature           | Priority |
| ------ | ----------------- | -------- |
| TM-011 | Subtasks          | P0       |
| TM-012 | Task Dependencies | P0       |
| TM-013 | Recurring Tasks   | P0       |
| TM-014 | Bulk Operations   | P0       |
| TM-015 | Dashboard Summary | P0       |
| TM-016 | Archive Tasks     | P0       |
| TM-017 | Task Templates    | P1       |
| TM-018 | Task Attachments  | P1       |
| TM-019 | Task Comments     | P1       |
| TM-020 | Activity History  | P1       |

---

# EPIC 2 – Knowledge Management

Planned after completion of the Task Management epic.

Key features:

* Markdown notes
* Wiki pages
* Attachments
* Cross-linking
* Search

---

# EPIC 3 – AI Assistant

Planned immediately after Knowledge Management.

Key features:

* Ollama
* Planning
* Summaries
* Semantic search
* Natural language commands

---

# EPIC 4 – Synchronization

* Generic sync engine
* Import/export
* Backup
* Restore
* Conflict resolution

---

# EPIC 5 – GitHub

* Authentication
* Issue synchronization
* Pull requests
* Project synchronization

---

# EPIC 6 – TickTick

* Authentication
* Two-way synchronization
* Mapping
* Conflict resolution

---

# EPIC 7 – Google Tasks

* Authentication
* Two-way synchronization

---

# EPIC 8 – Calendar

* Events
* Agenda
* Scheduling
* Reminders

---

# EPIC 9 – Email

* Inbox
* Search
* Compose
* Notifications

---

# EPIC 10 – Security Operations

* Wazuh
* Incidents
* Alerts
* Automation

---

# Release Objective

The current engineering objective is to complete every P0 item in EPIC 1 before beginning the next epic.

No new epics should start until the Task Management module is production-ready.
