# CLAUDE.md — seeknay.com

Guidance for Claude Code when working in this repository. This file is the canonical
AI guide; the `README.md` is for humans and links here.

## What this is

- **Live site:** https://seeknay.com
- **Repo:** `pbuffolino/seeknay747.github.io` — **PUBLIC**
- **Stack:** Jekyll 3.9.5 (via `github-pages` gem) + **Minimal Mistakes remote theme** (`remote_theme: mmistakes/minimal-mistakes`), skin `air`.
- **Hosting/deploy:** GitHub Pages builds automatically from the **`master`** branch. There is no separate deploy step — merging to `master` publishes the site.

## Public repo — security & privacy first

This repo is public; everything committed is world-readable forever (git history included).

- **Never commit secrets, API keys, tokens, or private credentials.**
- **Never commit private PII** (personal email, home address, phone, employer-confidential info). The `email:` field in `_config.yml` is intentionally blank — keep it that way.
- The Google Analytics ID (`G-C9JSC7H6WW`) is public by design — that's expected for client-side GA.
- See `ANTIPATTERNS.md` for the full "don't do this" list. See `.github/SECURITY.md` for vuln reporting.

## Local development

```bash
bundle install
bundle exec jekyll serve   # http://localhost:4000
```

`_config.yml` is **not** auto-reloaded — restart the server after editing it.

## Repository layout

- `_config.yml` — site config (author, social, analytics, plugins, defaults). Restart server after changes.
- `_posts/` — blog posts, filename `YYYY-MM-DD-title.md`.
- `_pages/` — static pages (`about.md`, `404.md`, archives).
- `_includes/` — partials that **override** matching theme files (e.g. `head/custom.html`, `analytics-providers/google-gtag.html`).
- `assets/css/main.scss` — imports the theme skin + local style overrides (glassmorphism, fonts).
- `assets/images/` — post images, avatar, favicon.
- `_data/navigation.yml` — main nav.
- `script/check-local.sh` — local front-matter, production build and HTML-Proofer checks.

## Remote theme — how to customize

The theme lives remotely; you cannot edit its files here. To change a theme partial,
**create a local file at the same path** and it overrides the remote one (e.g. drop
`_includes/footer.html` to override the theme footer). Prefer `_config.yml` skin/settings
before overriding files. Theme docs: https://mmistakes.github.io/minimal-mistakes/docs/configuration/

## Post conventions (match existing posts)

Front matter most posts use (see `_posts/2025-02-12-defense-in-depth.md` as a template):

```yaml
---
title: "Descriptive Title"
date: 2026-06-27T09:00:00-04:00
categories:
  - identity
  - career-development
tags:
  - iam
  - career-paths
excerpt: "One-sentence summary used in listings and social previews."
author_profile: true
read_time: true
share: true
related: true
toc: true            # table of contents for long posts
toc_sticky: true
last_modified_at: 2026-06-27T09:00:00-04:00
---
```

- `layout: single`, `comments: false`, `classes: wide` come from `defaults` in `_config.yml` — no need to repeat them.
- Newer posts favor `identity` / `career-development` categories. Keep categories/tags lowercase-hyphenated.
- For very long posts a **custom collapsible TOC** (HTML `<details>`) is sometimes used instead of the theme TOC — if a post sets `toc: false`, that is intentional; do not flip it back.

## Plugins / GitHub Pages constraint

GitHub Pages only runs plugins on its [whitelist](https://pages.github.com/versions/).
Adding a non-whitelisted gem (e.g. `jekyll-algolia`) does **nothing** on the live site.
Active plugins are listed in `_config.yml` under `plugins:`. Search uses **Lunr**
(`search_provider: lunr`), which is client-side and needs no backend.

## Skills (in `.claude/skills/`)

- **`new-post`** — scaffold a new post with correct filename + front matter.
- **`share-post`** — draft per-platform social copy (Bluesky / X / LinkedIn / TikTok) for a post.
- **`publish-post`** — validate, build, branch, commit, and open a PR (never pushes to `master` directly).

Typical flow: `new-post` → write content → `publish-post` → after merge, `share-post`.

## Local checks and independent Codex review

Owner policy (2026-11-03): run `script/check-local.sh` with reviewed Ruby 3.3 and
installed locked gems. It preserves front-matter validation, the production
build, root-relative proofing build and HTML/link/image checks. It never installs
software or publishes the site. Missing runtime/dependencies or failing checks
block acceptance; report them explicitly rather than claiming a pass.

Independent native Codex code and security reviewers review the exact candidate
SHA before merge; record their dispositions and actual local command results in
the PR. New source changes require fresh evidence. Hosted CI and dependency
auto-merge are removed. Dependabot still proposes updates, which require local
checks and Codex review. Preserve branch protections and GitHub Pages deployment
from `master`; no checks means no hosted execution, not proof of local success.
