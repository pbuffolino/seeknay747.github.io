# seeknay.com

Source for [**seeknay.com**](https://seeknay.com) — a personal tech blog on Identity & Access
Management, security, PowerShell, and career topics. Built with [Jekyll](https://jekyllrb.com/)
and the [Minimal Mistakes](https://mmistakes.github.io/minimal-mistakes/) remote theme, hosted
on GitHub Pages.

> **Working with Claude Code in this repo?** Start with [`CLAUDE.md`](./CLAUDE.md) and
> [`ANTIPATTERNS.md`](./ANTIPATTERNS.md).

## Tech stack

- **Jekyll 3.10.0** via the pinned `github-pages` 232 gem (pins versions to match GitHub Pages).
- **Minimal Mistakes** remote theme (`remote_theme: mmistakes/minimal-mistakes`), skin `air`.
- **Markdown (Kramdown)** for content, **Liquid** for templating, **SCSS** for style overrides.
- Client-side **Lunr** search. Plugins: `jekyll-paginate`, `jekyll-sitemap`, `jekyll-gist`,
  `jekyll-feed`, `jemoji`, `jekyll-include-cache`.

## Local development

```bash
bundle install
bundle exec jekyll serve   # http://localhost:4000
```

`_config.yml` is **not** hot-reloaded — restart the server after editing it.

## Repository layout

| Path | Purpose |
|---|---|
| `_config.yml` | Site config: author, social, analytics, plugins, defaults. |
| `_posts/` | Blog posts — `YYYY-MM-DD-title.md`. |
| `_pages/` | Static pages (`about`, `404`, archives). |
| `_includes/` | Local partials that override matching theme files. |
| `assets/css/main.scss` | Theme skin import + style overrides. |
| `assets/images/` | Post images, avatar, favicon. |
| `_data/navigation.yml` | Main navigation. |
| `script/check_front_matter.rb` | Local guard: required post front matter. |
| `script/check-local.sh` | Local build + front-matter + HTML-Proofer checks. |
| `.claude/skills/` | Authoring/publishing automations (see below). |

## Publishing a post

1. **Draft** — use the `new-post` skill (scaffolds the filename + front matter), then write the body.
2. **Publish** — use the `publish-post` skill: it validates front matter, builds locally, opens a
   PR (never pushes to `master` directly), with local build + link/image checks and independent Codex review.
3. **Merge** — once exact-head local checks and independent Codex code/security reviews pass and the PR is merged, GitHub Pages publishes from `master` automatically.
4. **Promote** — use the `share-post` skill to draft per-platform social copy.

## Deployment

GitHub Pages builds and deploys automatically from the **`master`** branch. There is no
separate deploy step. Only plugins on the
[GitHub Pages whitelist](https://pages.github.com/versions/) run on the live build.

## Security & privacy

This is a **public** repository. Never commit secrets, credentials, or private PII; the
`email:` field in `_config.yml` is intentionally blank. Dependencies are monitored by
Dependabot. Source checks run locally and Codex reviews changes before merge. To report a vulnerability, see
[`.github/SECURITY.md`](./.github/SECURITY.md).

## Configuration reference

[Minimal Mistakes configuration docs](https://mmistakes.github.io/minimal-mistakes/docs/configuration/).
Available skins: `default`, `air`, `aqua`, `contrast`, `dark`, `dirt`, `neon`, `mint`, `plum`, `sunrise`.

## Local validation environments

Run `script/check-local.sh native` with host Ruby 3.3 and installed gems, or
explicitly select `script/check-local.sh docker` for bounded local Linux/amd64
validation using an immutable official Ruby 3.3.13 image. Both run front matter,
production/proofing builds and HTML-Proofer. Docker mode installs gems only in
its isolated scratch, never mounts host credentials or the Docker socket, and
retains exact-source/runtime/dependency receipts under ignored
`vendor/local-checks/`. It requires a clean committed checkout, local Docker,
Python 3.9+ and 5 GiB free. Neither mode publishes the site or proves native Mac
acceptance. See [the canonical guide](CLAUDE.md) for limits and review requirements.
