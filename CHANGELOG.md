# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.0] - 2026-05-21

### Added

- First public release of `frida-legacy-compat`
- Automatic patching for `frida.core.Session.create_script()`
- Legacy bridge script detection and on-demand bundle compilation
- Bridge profile selection based on `frida.__version__`
- CLI entrypoint with `--doctor` support
- Bilingual documentation for GitHub and PyPI

### Changed

- Allow `frida < 17` projects to keep `import frida_legacy_compat` safely as a silent no-op
- Warn on import when `17.0 <= frida < 17.2` is detected, asking users to upgrade Frida
- Add an installation note describing the supported Frida ranges and the `full` extra
- Load legacy scripts only after bridge globals are attached, fixing `ReferenceError: 'Java' is not defined`
