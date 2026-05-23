# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project aims to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.1.0] - 2026-05-23

### Changed

- Make patch activation explicit so importing `frida_legacy_compat` no longer auto-patches `Session.create_script()`
- Require users to call `frida_legacy_compat.patch_frida()` when they want to enable the compatibility layer
- Stop restricting the installed `frida` version during package installation
- Emit localized warnings on both import and `patch_frida()` when the current Frida version is outside the recommended range
- Keep unsupported or unvalidated Frida versions non-fatal by warning and staying in no-op mode instead of raising
- Update README and release documentation to reflect the explicit patch workflow

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
- Emit localized warnings instead of raising when the detected Frida version is outside the supported range
- Add an installation note describing the supported Frida ranges and the `full` extra
- Load legacy scripts only after bridge globals are attached, fixing `ReferenceError: 'Java' is not defined`
