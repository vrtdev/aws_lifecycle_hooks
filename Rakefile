# frozen_string_literal: true

require 'puppetlabs_spec_helper/rake_tasks'
require 'puppet-syntax/tasks/puppet-syntax'
require 'puppet_blacksmith/rake_tasks' if Bundler.rubygems.find_name('puppet-blacksmith').any?
require 'github_changelog_generator/task' if Bundler.rubygems.find_name('github_changelog_generator').any?
require 'puppet-strings/tasks' if Bundler.rubygems.find_name('puppet-strings').any?

def changelog_user
  return unless Rake.application.top_level_tasks.include? 'changelog'

  return_val = nil || JSON.parse(File.read('metadata.json'))['author']
  raise 'unable to find the changelog_user in .sync.yml, or the author in metadata.json' if return_val.nil?

  puts "GitHubChangelogGenerator user:#{return_val}"
  return_val
end

def changelog_project
  return unless Rake.application.top_level_tasks.include? 'changelog'

  return_val = nil || JSON.parse(File.read('metadata.json'))['name']
  raise 'unable to find the changelog_project in .sync.yml or the name in metadata.json' if return_val.nil?

  puts "GitHubChangelogGenerator project:#{return_val}"
  return_val
end

def changelog_future_release
  return unless Rake.application.top_level_tasks.include? 'changelog'

  return_val = 'v%s'.format(JSON.parse(File.read('metadata.json'))['version'])
  raise 'unable to find the future_release (version) in metadata.json' if return_val.nil?

  puts "GitHubChangelogGenerator future_release:#{return_val}"
  return_val
end

PuppetLint.configuration.send('disable_relative')

if Bundler.rubygems.find_name('github_changelog_generator').any?
  GitHubChangelogGenerator::RakeTask.new :changelog do |config|
    raise "Set CHANGELOG_GITHUB_TOKEN environment variable eg 'export CHANGELOG_GITHUB_TOKEN=valid_token_here'" if Rake.application.top_level_tasks.include?('changelog') && ENV['CHANGELOG_GITHUB_TOKEN'].nil?

    config.user = changelog_user.to_s
    config.project = changelog_project.to_s
    config.future_release = changelog_future_release.to_s
    config.exclude_labels = ['maintenance']
    config.header = "# Change log\n\nAll notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](http://semver.org)."
    config.add_pr_wo_labels = true
    config.issues = false
    config.merge_prefix = '### UNCATEGORIZED PRS; GO LABEL THEM'
    config.configure_sections = {
      'Changed' => {
        'prefix' => '### Changed',
        'labels' => ['backwards-incompatible']
      },
      'Added' => {
        'prefix' => '### Added',
        'labels' => %w[feature enhancement]
      },
      'Fixed' => {
        'prefix' => '### Fixed',
        'labels' => ['bugfix']
      }
    }
  end
else
  desc 'Generate a Changelog from GitHub'
  task :changelog do
    raise <<~ENDOFMESSAGE
      The changelog tasks depends on unreleased features of the github_changelog_generator gem.
      Please manually add it to your .sync.yml for now, and run `pdk update`:
      ---
      Gemfile:
        optional:
          ':development':
            - gem: 'github_changelog_generator'
              git: 'https://github.com/skywinder/github-changelog-generator'
              ref: '20ee04ba1234e9e83eb2ffb5056e23d641c7a018'
              condition: "Gem::Version.new(RUBY_VERSION.dup) >= Gem::Version.new('2.2.2')"
    ENDOFMESSAGE
  end
end
