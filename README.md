# seeknay.com

This repository contains the source code for [seeknay.com](https://seeknay.com), a personal tech blog built with Jekyll and hosted on GitHub Pages.

## Project Overview

*   **Type:** Personal Blog / Portfolio
*   **Engine:** [Jekyll](https://jekyllrb.com/)
*   **Theme:** [Minimal Mistakes](https://mmistakes.github.io/minimal-mistakes/) (Remote Theme)
*   **Hosting:** GitHub Pages

## Architecture & Tech Stack

The site leverages the power of static site generation via Jekyll, utilizing a remote theme for styling and layout to keep the codebase clean and maintainable.

### Key Technologies
*   **Ruby:** The underlying language for Jekyll.
*   **Liquid:** Templating language used for dynamic content insertion.
*   **Markdown (Kramdown):** Used for authoring content (posts and pages).
*   **YAML:** Used for configuration (`_config.yml`) and Front Matter data.
*   **SCSS:** The theme uses SCSS, though this repo currently relies on the standard theme assets.

### Directory Structure
*   `_config.yml`: **Critical.** The central configuration file. Controls site settings, author info, navigation, and plugins. **Note:** Changes here require a server restart.
*   `_posts/`: Contains blog posts. Format: `YYYY-MM-DD-title.md`.
*   `_pages/`: Contains static pages (e.g., `about.md`, `404.md`, Archives).
*   `_includes/`: HTML partials. Contains a custom overrides like `analytics-providers/google-gtag.html`.
*   `assets/`: Currently stores images in `images/`.
*   `Gemfile`: Define Ruby gem dependencies.

## Development Instructions

### formatting
*   **Line Endings:** Use standard LF.
*   **Encoding:** UTF-8.

### AI Coding Guidelines
When acting as an AI assistant for this repository, please adhere to the following:

1.  **Content Creation:**
    *   New posts must go into `_posts/` with the filename format `YYYY-MM-DD-title.md`.
    *   Ensure valid YAML Front Matter (title, date, categories, tags).
    *   Use `classes: wide` in Front Matter or defaults if a wide layout is preferred.

2.  **Configuration Management:**
    *   All global settings (Title, Description, Author links, Sidebars) are managed in `_config.yml`.
    *   When modifying `_config.yml`, remind the user that a local server restart is required.

3.  **Theme Customization:**
    *   **Do not** try to edit theme files directly as they are loaded remotely.
    *   **To Override:** Create a file with the same path and name in the local directory (e.g., `_includes/head.html` to override the theme's head).
    *   **Custom CSS:** If requested, create `assets/css/main.scss` and import the theme's CSS specifically to add overlays, but prefer using `_config.yml` skin settings first.

4.  **Plugins:**
    *   Supported plugins are listed in `Gemfile` under `github-pages` or `jekyll_plugins`.
    *   Current plugins: `jekyll-paginate`, `jekyll-sitemap`, `jekyll-gist`, `jekyll-feed`, `jemoji`, `jekyll-include-cache`, `jekyll-algolia`.

### Local Execution
To run the site locally:
```bash
bundle install
bundle exec jekyll serve
```
Access via `http://localhost:4000`.

## Deployment
The site is deployed automatically via GitHub Pages when changes are pushed to the default branch.

## Configuration Resources
For detailed configuration options, refer to the [Minimal Mistakes Configuration Documentation](https://mmistakes.github.io/minimal-mistakes/docs/configuration/).

### Quick Reference
*   **Skins:** `default`, `air`, `aqua`, `contrast`, `dark`, `dirt`, `neon`, `mint`, `plum`, `sunrise`
*   **Locale:** Defined in `_config.yml` (e.g., `en-US`). Matches `_data/ui-text.yml`.
*   **Search:** Enabled via `search: true`.
