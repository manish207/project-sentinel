# Project Sentinel Planning System

This directory contains the complete planning and engineering documentation for Project Sentinel.

## Objectives

* Keep the GitHub repository as the single source of truth.
* Track product evolution through milestones and GitHub Projects.
* Define engineering standards before implementation.
* Record architectural decisions.
* Manage releases, risks, and technical debt.
* Enable contributors to understand the project without external documentation.

## Directory Structure

### product/

Product vision, roadmap, MVP definition, and feature planning.

### engineering/

Coding standards, development workflow, testing standards, branching strategy, and contribution guidelines.

### architecture/

High-level architecture documents and Architecture Decision Records (ADRs).

### security/

Security policies, threat modeling, credential handling, and security backlog.

### releases/

Release planning, milestones, and version strategy.

### backlog/

Product backlog, epics, feature decomposition, and implementation priorities.

### import/

Files intended for GitHub CLI or GitHub API imports, including labels, milestones, and issues.

### reports/

Generated reports such as architecture reviews, technical debt analysis, performance reports, and release readiness.

## Guiding Principles

1. Local-first.
2. API-first.
3. Plugin-first.
4. AI-assisted.
5. Test-driven.
6. Security by design.
7. Documentation as code.
8. Continuous integration for every change.

## Repository Workflow

1. Create or update a GitHub Issue.
2. Assign the issue to a milestone.
3. Move the issue to the GitHub Project board.
4. Implement on a feature branch.
5. Ensure CI passes.
6. Open a Pull Request.
7. Merge into `main`.
8. Update documentation if architecture or behavior changes.

This planning system is intended to evolve alongside the codebase and should be maintained as part of normal development.
