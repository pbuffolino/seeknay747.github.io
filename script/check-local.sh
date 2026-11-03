#!/usr/bin/env bash
# Source validation only. This does not publish or install Ruby/gems.
set -euo pipefail
cd "$(dirname "$0")/.."
ruby -e 'abort "Use the reviewed Ruby 3.3 runtime; no software is installed by this check." unless RUBY_VERSION.split(".").first(2) == ["3", "3"]'
bundle check
ruby script/check_front_matter.rb
JEKYLL_ENV=production bundle exec jekyll build
JEKYLL_ENV=production bundle exec jekyll build --config _config.yml,_config_proofer.yml
bundle exec htmlproofer ./_site --disable-external --allow-hash-href --allow-missing-href --ignore-missing-alt
printf 'Local source checks passed. Record exact commit, toolchain and independent Codex reviews before merge.\n'
