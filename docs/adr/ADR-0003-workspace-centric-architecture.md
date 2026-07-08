# ADR-0003 — Workspace-Centric Architecture

**Status:** Accepted

**Date:** 2026-07-07

---

# Context

Project Sentinel aims to become a unified productivity platform rather than a standalone task manager.

Future modules include:

* Tasks
* Projects
* Notes
* Documents
* Calendar
* Email
* GitHub
* TickTick
* Google Tasks
* Wazuh
* AI

These modules should not evolve independently.

---

# Decision

Workspace is the primary domain boundary.

Every major entity belongs to exactly one Workspace.

Projects become optional organizational containers.

Tasks may belong to:

* a project
* or directly to a workspace

Notes, documents, calendar events, AI memory, contacts, and future modules also belong to the workspace.

---

# Domain Model

Workspace

├── Projects

├── Tasks

├── Notes

├── Documents

├── Calendar Events

├── Contacts

├── Files

├── Knowledge Base

├── AI Memory

└── Integrations

---

# Relationships

Projects organize work.

Tasks represent actionable work.

Notes capture knowledge.

Calendar events represent time.

Files provide supporting material.

AI Memory stores embeddings, summaries, and learned context.

Integrations synchronize external systems.

---

# Benefits

* Consistent ownership model.
* Simpler authorization.
* Easier backup and restore.
* Clear synchronization boundaries.
* Scalable plugin architecture.
* Better AI context.
* Improved search capabilities.

---

# Consequences

Every future module must declare a Workspace owner.

Projects are optional.

The Workspace becomes the root aggregate for data organization and lifecycle management.
