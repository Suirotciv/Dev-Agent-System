# EVIDENCE.md

This file records the reasoning behind the template's major design choices.

## Shared State

The system uses `.agents/STATE.json` as the current snapshot because chat
history is fragile across sessions. A small JSON file is easy for agents and
humans to inspect, diff, and repair.

## Role Separation

Orchestrator, Feature Agent, and Verifier roles are intentionally separate.
The builder should not be the only judge of whether the feature works. Gate
artifacts preserve what was checked and when.

## Append-Only Artifacts

Session logs, update envelopes, and gate artifacts act as the audit trail. They
are append-only so failed attempts remain visible and can be converted into
future tests.

## Stdlib-Only Tooling

The helper scripts avoid third-party dependencies so a new solo developer can
clone the template and run validation immediately with Python.
