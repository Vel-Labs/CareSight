# Docs Index

## Directory structure

```text
docs/
  README.md
  agents/
  architecture/
  decisions/
  project/
    TEMPLATE_USAGE.md
  repo-truth/
  governance/
  hackathon/
  operations/
  roadmaps/
  templates/
  audits/
hackathon/     judge/operator entrypoint for the current demo
```

Root-level implementation and quality directories:

```text
contracts/      canonical project truth
packages/core/  reusable executable enforcement
tests/          shared local quality gate
skills/         repo-local skills with SKILL.md and optional templates
REPO_PROFILE.json machine-readable taxonomy and command index
```

## Reading paths

### New contributor

1. `../README.md`
2. `../AGENTS.md`
3. `../REPO_PROFILE.json`
4. `agents/START_HERE.md`
5. `project/TEMPLATE_USAGE.md`
6. `../contracts/README.md`
7. `../packages/core/README.md`
8. `../tests/README.md`
9. `architecture/ARCHITECTURE.md`
10. `architecture/REPO_BOUNDARIES.md`
11. `../ROADMAP.md`
12. `../DECISIONS.md`
13. `roadmaps/CURRENT_STATE_AND_NEXT.md`
14. `repo-truth/THC_METHODOLOGY.md`
15. `governance/code-quality-standards.md`
16. `roadmaps/README.md`

### Baseline verification

```bash
npm run validate:scaffold
npm run validate:contracts
npm run test:focused
npm test
npm run typecheck
```

### Hackathon project

1. `../hackathon/README.md`
2. `../hackathon/DEMO_JOURNEY.md`
3. `../hackathon/AUDIT_DIGEST.md`
4. `project/PROJECT_BRIEF.md`
5. `getting_started.md`
6. `operations/local_model_operations.md`
7. `hackathon/README.md`
8. `hackathon/rules.md`
9. `hackathon/vendor-tracks.md`
10. `hackathon/submission-checklist.md`

### Current state and cleanup

1. `roadmaps/CURRENT_STATE_AND_NEXT.md`
2. `audits/2026-05-23-hackathon-state-and-cleanup-plan.md`
3. `cli/COMMANDS.md`
4. `architecture/camera_integration_strategy.md`
