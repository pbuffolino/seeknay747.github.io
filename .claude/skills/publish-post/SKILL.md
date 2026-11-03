---
name: publish-post
description: Validate, build, and open a pull request for a finished seeknay.com blog post or site change. Use when the user wants to publish, ship, release, or PR a post/change. Never pushes directly to master.
---

# Publish Post

Take a finished change from the working tree to a reviewable PR. `master` is the deploy
branch and is protected — **always go through a PR, never push to `master` directly.**

## Steps

1. **Run the complete local gate** using the reviewed Ruby 3.3 runtime and installed locked gems:
   ```bash
   script/check-local.sh
   ```
   This checks front matter, production build, root-relative build and HTML-Proofer.
   Missing prerequisites or failures block release. Do not install software implicitly.

2. **Obtain independent native Codex code and security review** of the exact candidate
   revision. Record actual local command results and review dispositions in the PR;
   refresh evidence after changing source. The implementing agent does not approve itself.

3. **Branch** off `master` if not already on a feature branch:
   ```bash
   git checkout -b post/<slug-or-topic>
   ```

4. **Commit** with a conventional message:
   ```bash
   git add -A
   git commit -m "feat(blog): <post title>"
   ```
   (Use `chore:`/`fix:`/`docs:` for non-post changes.)

5. **Push and open a PR**:
   ```bash
   git push -u origin HEAD
   gh pr create --base master --fill
   ```
   The PR must contain passing exact-head local check evidence and independent Codex reviews before merge. Hosted CI is intentionally absent; never treat that absence as validation.

6. **Report** the PR URL back to the user. After they merge, GitHub Pages publishes from
   `master` automatically — then suggest the **share-post** skill.

## Guardrails
- Never `git push` to `master` directly; never use `--no-verify` or bypass branch protection.
- Confirm the working tree contains only intended changes (`git status`) before committing.
- This is a PUBLIC repo: re-check the diff for secrets/PII before pushing.
- If the build or checks fail, stop and surface the error — don't force the PR through.
