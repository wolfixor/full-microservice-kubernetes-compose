# Project Docs

Start with [START-HERE.md](START-HERE.md) when something is broken or you need a fast map.

The implementation sequence and current learning status live in
[roadmap.md](roadmap.md).

Production rule: raw YAML is okay for learning and emergency drills, but the production direction is Helm/Kustomize/GitOps plus operators, with no downtime by default for existing services.

Docs are split by purpose:

- [Architecture](architecture/README.md): current state, apply flow, and CRD map.
- [Concepts](concepts/README.md): what each stack/component does and how the flow works.
- [Commands](commands/README.md): commands, configs, checks, tests, and recovery steps.
