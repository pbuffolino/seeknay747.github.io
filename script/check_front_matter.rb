#!/usr/bin/env ruby
# frozen_string_literal: true

# Local guard: every published post in _posts/ must have the required front matter.
# Keeps listings, SEO, and archives from silently breaking.

require "yaml"
require "date"

REQUIRED = %w[title date categories tags].freeze
POSTS_DIR = File.expand_path("../_posts", __dir__)

errors = []

Dir.glob(File.join(POSTS_DIR, "*.{md,markdown}")).sort.each do |path|
  name = File.basename(path)
  raw = File.read(path)

  unless raw.start_with?("---")
    errors << "#{name}: missing YAML front matter block"
    next
  end

  # Front matter is between the first two '---' lines.
  parts = raw.split(/^---\s*$/, 3)
  front = parts[1]
  if front.nil? || front.strip.empty?
    errors << "#{name}: empty front matter"
    next
  end

  begin
    data = YAML.safe_load(front, permitted_classes: [Date, Time], aliases: true) || {}
  rescue Psych::SyntaxError => e
    errors << "#{name}: invalid YAML front matter (#{e.message})"
    next
  end

  REQUIRED.each do |key|
    value = data[key]
    if value.nil? || (value.respond_to?(:empty?) && value.empty?)
      errors << "#{name}: missing or empty required key '#{key}'"
    end
  end
end

if errors.empty?
  puts "Front matter check passed for all posts in _posts/."
  exit 0
else
  warn "Front matter check FAILED:"
  errors.each { |e| warn "  - #{e}" }
  exit 1
end
