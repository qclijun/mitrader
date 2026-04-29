# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Layout

This is a single-context repo. Use one root `CONTEXT.md` for domain vocabulary and `docs/adr/` for architectural decision records when those files exist.

## Before exploring, read these

- `CONTEXT.md` at the repo root.
- `docs/adr/` for ADRs related to the area being changed.

If these files do not exist, proceed silently. Do not flag their absence or suggest creating them upfront.

## Use the glossary's vocabulary

When output names a domain concept in an issue title, refactor proposal, hypothesis, or test name, use the term as defined in `CONTEXT.md`. If the needed concept is missing, note the gap for a future documentation pass.

## Flag ADR conflicts

If output contradicts an existing ADR, surface the conflict explicitly instead of silently overriding it.
