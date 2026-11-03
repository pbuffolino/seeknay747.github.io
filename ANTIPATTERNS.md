# Antipatterns — seeknay.com

Things **not** to do in this repo, with the reasoning. Grounded in how this specific
Jekyll + Minimal Mistakes (remote theme) + GitHub Pages site is built.

## Security & privacy (PUBLIC repo)

- ❌ **Don't commit secrets** — API keys, tokens, passwords, `.env` files. Git history is public and permanent; rotating a leaked key is the only fix.
- ❌ **Don't commit private PII** — keep `email:` blank in `_config.yml`; don't paste personal email/phone/address into posts or config. Use the contact options already on the site.
- ❌ **Don't paste employer-confidential or client material** into posts. Generalize examples.
- ✅ The GA4 ID and public social handles are fine to commit — they're meant to be public.

## Theme & build

- ❌ **Don't edit `_site/`** — it's generated output (gitignored). Edit sources, then rebuild.
- ❌ **Don't try to edit the Minimal Mistakes theme files** — they're loaded remotely. To change one, create a local file at the **same path** to override it.
- ❌ **Don't add a plugin and expect it to run on GitHub Pages** unless it's on the [Pages whitelist](https://pages.github.com/versions/). Non-whitelisted gems are silently ignored on the live build.
- ❌ **Don't reintroduce `jekyll-algolia`** — it's not whitelisted, so it does nothing on the live site. Search runs on **Lunr** (`search_provider: lunr`).
- ⚠️ **Restart `jekyll serve` after editing `_config.yml`** — it is not hot-reloaded; changes appear to "not work" otherwise.

## Content / front matter

- ❌ **Don't omit required front matter** — every post needs `title`, `date`, `categories`, `tags`. A missing field breaks listings/SEO and fails the local front-matter gate.
- ❌ **Don't flip `toc: false` back to `true` blindly** — some long posts (e.g. the 2026 IAM job-market post) intentionally use a custom collapsible `<details>` TOC instead of the theme's sticky TOC.
- ❌ **Don't use future or mismatched dates** in the filename vs. front matter — Jekyll won't publish future-dated posts in production until that date.
- ✅ Keep categories/tags lowercase-hyphenated and consistent with existing taxonomy.

## Workflow & repo hygiene

- ❌ **Don't push directly to `master`** for content changes — `master` is the deploy branch and is protected. Open a PR after local build + HTML-Proofer checks and independent Codex review. Use the `publish-post` skill.
- ❌ **Don't bypass local checks or independent Codex review** to "just ship it" — the build/link checks are the safety net for a site with no staging environment.
- ❌ **Don't hand-edit `assets/social-metrics`-style generated files** if any are added later by automation.
- ✅ Let Dependabot PRs update `github-pages` / gem and Action versions; review and merge them.
