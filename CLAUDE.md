# CLAUDE.md - TPA Codebase Guide

Detailed guides for working on this codebase are maintained on the
`claude/agent-docs` branch. Read them without switching branches:

    git show claude/agent-docs:CLAUDE.md
    git show claude/agent-docs:agent-docs/QUICK-REFERENCE.md
    git show claude/agent-docs:agent-docs/PR-WORKFLOW.md
    git show claude/agent-docs:agent-docs/VERIFICATION-GUIDE.md

Available guides:

- **CLAUDE.md** — Full codebase overview with navigation
- **QUICK-REFERENCE.md** — Commands, file locations, cheat sheet
- **PR-WORKFLOW.md** — Branch naming, commits, release notes, pre-PR checklist
- **VERIFICATION-GUIDE.md** — What to test based on what you changed
- **CONFIGURE-DEVELOP.md** — Python architecture code (lib/tpa/, lib/tpaexec/)
- **DEPLOY-ROLES.md** — Ansible roles and deployment
- **CONFIG-YML-REFERENCE.md** — Annotated config.yml examples
- **AWS-DEPLOYMENT.md** — AWS-specific requirements and workflows
- **GETTING-STARTED.md** — Hands-on walkthrough for new developers
- **AGENT-GUIDE-AWS-TPA-HOST.md** — Running TPA on AWS instances
- **TESTING-MATRIX.md** — Minimal effective deployment test matrix per change type

## Maintaining Agent Docs

All agent documentation lives on the `claude/agent-docs` branch.
To add or update guides, commit to that branch — not to `main` or
any working branch.

## Essential Conventions

### Ticket first

- Before starting any code change, confirm a Jira ticket exists for the work
- Ask for the ticket number (e.g., `TPA-1234`) — it drives branch name, commit references, release notes, and PR title

### Branch naming

- `dev/TPA-XXX-short-description` (triggers Jira auto-sync)

### Commit messages

- Summary: imperative mood, initial capital, <60 chars, no trailing period
- Body: explain why, include `References: TPA-XXXX`
- Footer: `Co-Authored-By: Claude <model> <noreply@anthropic.com>`
- No GitHub @mentions

### Release notes

- For user-visible changes, create `release_notes/TPA-XXXX.yml`
- Customer-focused, output-focused, summary starts with action verb
- Template: `release_notes/relnote.yml.template`

### Code formatting

- Python: must be formatted with Black
- Verify: `tox -e py312-lint`

### Before submitting

- Tests: `tox -e py312-test`
- Lint: `tox -e py312-lint`
- New files: copyright header (check existing files for format)
- Release note if change is user-visible
- Docs: update `docs/src/*.md` if change affects user-facing behavior
- PRs: always create in draft mode (`gh pr create --draft`)
- Test report: post results as comment on draft PR with summarized conclusion
- PR body: include `🤖 Generated with [Claude Code](https://claude.com/claude-code)`
