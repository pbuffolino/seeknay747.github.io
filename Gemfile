source "https://rubygems.org"

gem "github-pages", "233", group: :jekyll_plugins

gem "tzinfo-data"
gem "wdm", "~> 0.1.0" if Gem.win_platform?

# If you have any plugins, put them here!
group :jekyll_plugins do
  gem "jekyll-paginate"
  gem "jekyll-sitemap"
  gem "jekyll-gist"
  gem "jekyll-feed"
  gem "jemoji"
  gem "jekyll-include-cache"
end

gem "webrick", "~> 1.9"

# Local validation: link/image/HTML checks against the built _site.
# Not used by the GitHub Pages build (Pages ignores non-whitelisted gems).
group :test do
  gem "html-proofer", "~> 5.0"
end
