# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
when practical.

## [Unreleased]

## [0.1.1] - 2026-06-17

### Added
- Print top-level `output` field from `results.json` as an info message after each run

### Fixed
- Use `--mount type=bind,...` instead of `-v` for Docker volume mounts to fix path parsing on Windows (Git Bash MSYS mangling and drive-letter colon ambiguity)

## [0.1.0] - 2026-05-02

### Added
- First public release of `gslocal`
- Initial project scaffolding for running Gradescope autograders locally
- `gslocal init` command for generating project configuration
- `gslocal run` command for building and executing autograders against submissions
- `gslocal clean` command for removing local project state
- Support for zip, local directory, and GitHub repository submissions
- Build and Docker image caching to speed up repeated runs
- Formatted terminal output for autograder results

### Changed
- Initial project documentation, contribution docs, and release automation
