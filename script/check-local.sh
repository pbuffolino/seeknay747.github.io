#!/usr/bin/env bash
# Source validation only. Select native explicitly or an isolated local Docker gate.
set -euo pipefail
cd "$(dirname "$0")/.."
case "${1:-native}" in
  native) ;;
  docker) exec python3 script/check-local-docker.py ;;
  *) echo 'usage: script/check-local.sh [native|docker]' >&2; exit 2 ;;
esac
ruby -e 'abort "Use the reviewed Ruby 3.3 runtime; no software is installed by this check." unless RUBY_VERSION.split(".").first(2) == ["3", "3"]'
bundle check
ruby script/check_front_matter.rb
JEKYLL_ENV=production bundle exec jekyll build
JEKYLL_ENV=production bundle exec jekyll build --config _config.yml,_config_proofer.yml
bundle exec htmlproofer ./_site --disable-external --allow-hash-href --allow-missing-href --ignore-missing-alt
printf 'Local source checks passed. Record exact commit, toolchain and independent Codex reviews before merge.\n'
