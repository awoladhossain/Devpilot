# GitHub Workflow Guide

> Practical notes for working with Git, GitHub CLI, GitHub Actions, Pull Requests, and Squash Merge.

## 1. GitHub CLI Authentication

GitHub CLI (`gh`) lets us manage pull requests, inspect CI checks, and interact with GitHub directly from the terminal.

### Authenticate

```bash
gh auth login
```

Recommended choices:

- GitHub.com
- SSH for Git operations
- Skip SSH key upload if the key is already configured
- Login with a web browser

### Verify Authentication

```bash
gh auth status
```

Expected result: logged in to GitHub with the intended account.

**Important:** SSH authentication for Git and GitHub CLI authentication are separate. A successful `git push` does not automatically mean `gh` is authenticated.

---

## 2. GitHub Actions CI

CI stands for **Continuous Integration**. It automatically runs checks against code changes to help catch problems before merging.

Example workflow location:

```text
.github/workflows/ci.yml
```

Example workflow:

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v10.3.2
      - run: uv sync --locked
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run pytest
```

### What each step does

| Step | Purpose |
|---|---|
| `actions/checkout` | Checks out the repository code |
| `astral-sh/setup-uv` | Installs and configures uv |
| `uv sync --locked` | Installs dependencies using the lockfile |
| `uv run ruff check .` | Checks code for linting errors |
| `uv run ruff format --check .` | Verifies formatting without changing files |
| `uv run pytest` | Runs automated tests |

### What does CI green mean?

A green CI status means the configured checks passed.

It does **not** automatically guarantee that:

- The implementation is correct for every use case.
- The code is secure.
- The design is maintainable.
- The PR has been reviewed.

Always review the diff before merging.

---

## 3. Creating a Pull Request

Suppose the feature branch is:

```text
chore/ci-pipeline
```

### Check the current branch

```bash
git branch --show-current
```

### Check repository status

```bash
git status
```

### Push the branch

```bash
git push -u origin chore/ci-pipeline
```

### Create a PR

```bash
gh pr create --fill
```

A Pull Request (PR) proposes merging changes from a source branch into a target branch, usually `main`.

For this project:

```text
Source: chore/ci-pipeline
Target: main
```

---

## 4. Reviewing a Pull Request

Before merging, inspect the actual changes.

### Check PR status

```bash
gh pr status
```

### View the diff

```bash
gh pr diff
```

The diff shows which lines were added, removed, or modified.

### Open the PR in a browser

```bash
gh pr view --web
```

### Review checklist

- [ ] The changes solve the intended problem.
- [ ] No unrelated files were changed.
- [ ] No secrets, passwords, tokens, or private keys were committed.
- [ ] Dependencies and lockfiles are consistent.
- [ ] Configuration changes are intentional.
- [ ] The code is readable and maintainable.
- [ ] Appropriate tests exist for the changes.
- [ ] No obvious security or correctness issues remain.

For a CI configuration PR, pay special attention to:

- `.github/workflows/ci.yml`
- `pyproject.toml`
- `uv.lock`
- Test configuration and dependency groups

---

## 5. Checking CI Results

```bash
gh pr checks
```

This command shows the checks associated with the PR.

Possible states include:

- **Pass:** The check succeeded.
- **Fail:** The check failed and should be investigated.
- **Pending:** The check is still running or waiting.

Do not merge while required checks are failing or pending.

If CI fails, inspect the failure logs in GitHub Actions, fix the problem, commit the changes, and push again.

---

## 6. Understanding Squash Merge

A Squash Merge combines the commits in a PR into one commit on the target branch.

Example:

Before squash merge:

```text
main:       A --- B
                 \
feature:          C --- D --- E
```

After squash merge:

```text
main:       A --- B --- S
```

Here, `S` represents one commit containing the combined PR changes.

### Why use Squash Merge?

- Keeps the main branch history concise.
- Combines small corrective commits into one logical change.
- Makes it easier to understand when a feature was introduced.

### Merge only after review

```bash
gh pr diff
gh pr checks
```

Once the diff is reviewed and all required checks pass:

```bash
gh pr merge --squash
```

To delete the remote feature branch after merging, if desired:

```bash
gh pr merge --squash --delete-branch
```

Use branch deletion only when you no longer need that remote branch.

---

## 7. Verifying the Merge

```bash
gh pr view --json state,mergedAt,url
```

A successfully merged PR should report:

```text
state: MERGED
```

Then update the local `main` branch:

```bash
git switch main
git pull origin main
```

Check the latest commits:

```bash
git log --oneline -5
```

---

## 8. Fixing a GitHub Actions Version Error

Example error:

```text
Unable to resolve action 'astral-sh/setup-uv@5'
```

The action reference is invalid or cannot be resolved.

### How to troubleshoot

1. Open the official action repository.
2. Verify the available release tags.
3. Update the workflow to use a valid version.
4. Commit and push the change.
5. Check CI again.

Official repository:

https://github.com/astral-sh/setup-uv

Always verify that a version tag exists before using it. The example version in this document may need updating as releases change.

---

## 9. Common GitHub Commands

| Command | Purpose |
|---|---|
| `git status` | Inspect working-tree changes |
| `git branch --show-current` | Show the current branch |
| `git diff` | Inspect uncommitted changes |
| `git log --oneline -5` | View recent commits |
| `git push` | Push commits to the remote |
| `gh auth status` | Check CLI authentication |
| `gh pr status` | Show PRs relevant to the repository |
| `gh pr view --web` | Open the current PR in a browser |
| `gh pr diff` | Inspect PR changes |
| `gh pr checks` | Inspect CI checks |
| `gh pr merge --squash` | Squash-merge the PR |
| `git switch main` | Switch to `main` |
| `git pull origin main` | Update local `main` |

---

## 10. Recommended PR Workflow

Use this sequence for routine changes:

1. Create a dedicated feature branch.
2. Implement the change.
3. Run relevant tests and linting locally.
4. Commit and push the branch.
5. Open a Pull Request.
6. Review the diff yourself.
7. Wait for required CI checks to pass.
8. Fix any issues and push updates if needed.
9. Squash-merge after review and required approvals.
10. Update local `main`.

**Core principle:** Green CI + reviewed diff + required approvals = ready to merge.
