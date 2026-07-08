# Project Sentinel MVP

Version: 1.0

---

# Purpose

The Minimum Viable Product (MVP) defines the smallest version of Project Sentinel that provides real value for day-to-day personal productivity.

The MVP is successful when the primary user can rely on Sentinel every day without needing multiple separate applications for core planning and task management.

---

# MVP Goal

Provide a reliable, local-first productivity platform that enables a user to:

* Organize work
* Track projects
* Manage tasks
* Take notes
* Search information
* Synchronize with selected external services
* Receive AI assistance
* Maintain complete ownership of their data

---

# Target User

Primary target:

* Individual software engineer
* Cybersecurity professional
* Technical project owner
* Power user

Secondary target:

* Small technical teams (future releases)

---

# In Scope

## Core Productivity

* Workspaces
* Projects
* Tasks
* Subtasks
* Tags
* Due dates
* Priorities
* Recurring tasks
* Search
* Filters
* Notes
* Attachments
* Dashboard

---

## Local Storage

* SQLite
* Automatic backups
* Restore
* Import/export
* Data migration

---

## Synchronization

* Generic sync framework
* GitHub
* TickTick
* Google Tasks

Synchronization must support:

* Import
* Export
* Two-way synchronization
* Conflict detection
* Conflict resolution

---

## AI

Local AI through Ollama.

Capabilities:

* Natural language task creation
* Task decomposition
* Prioritization suggestions
* Daily planning
* Summaries
* Semantic search

Cloud AI providers are optional and must never be required.

---

## Knowledge Management

* Markdown notes
* Wikis
* Cross-links
* Attachments
* Full-text search

---

## Security Operations

Basic Wazuh integration:

* Alert listing
* Incident tracking
* Playbooks
* Investigation notes

---

## User Interface

Provide:

* CLI
* REST API
* Responsive web application

Desktop and mobile applications are post-MVP.

---

# Non-Goals

The MVP does not include:

* Multi-user collaboration
* Marketplace
* Billing
* SaaS deployment
* Enterprise administration
* Advanced analytics
* Real-time collaboration
* Plugin marketplace

---

# Quality Requirements

The MVP must include:

* Automated testing
* Continuous Integration
* Type checking
* Documentation
* Structured logging
* Configuration management
* Backup and restore
* Error handling

---

# Success Metrics

The MVP is considered successful when:

* Sentinel is used as the primary daily task manager.
* Daily planning occurs entirely within Sentinel.
* Tasks synchronize reliably with configured providers.
* AI assistance reduces manual task organization.
* Backups and restores are dependable.
* Users can work offline for extended periods.

---

# Exit Criteria

The MVP is complete only when all of the following are true:

* Core task management is stable.
* Synchronization framework is production-ready.
* At least one external provider is fully supported.
* AI planning is functional.
* Notes and knowledge management are usable.
* CI pipeline is stable.
* Documentation is complete.
* No critical defects remain.

---

# Guiding Principle

A smaller, reliable product is more valuable than a larger, unfinished one.

Every feature included in the MVP must be something the user can depend on every day.
