# frida-legacy-compat

[![Repository](https://img.shields.io/badge/GitHub-RYF5584%2Ffrida--legacy--compat-181717?logo=github)](https://github.com/RYF5584/frida-legacy-compat)
[![GitHub stars](https://img.shields.io/github/stars/RYF5584/frida-legacy-compat?style=social)](https://github.com/RYF5584/frida-legacy-compat/stargazers)

[简体中文](./README.zh-CN.md) | [English](./README.en.md)

`frida-legacy-compat` is a compatibility layer for Frida 17+ that restores a
Frida 16-style `session.create_script()` workflow for Python users.

This package is specifically meant to solve the Frida 17.0.0+ Python API bridge
issue where running legacy JavaScript through `session.create_script()` may
fail with:

```python
{'type': 'error', 'description': "ReferenceError: 'Java' is not defined", 'stack': "ReferenceError: 'Java' is not defined\n at (/script1.js:3)"}
```

Since Frida 17, the old bridge-based plain JavaScript workflow is no longer
available by default. In many cases users must switch to TypeScript/ESM builds
or download bridges separately, which makes the simple Python injection path
much less convenient.

This package is the one-step fix:

- install once
- add `import frida_legacy_compat`
- call `frida_legacy_compat.patch_frida()` explicitly
- keep passing legacy JavaScript strings to `session.create_script(source)`
- keep using `Java`, `ObjC`, and `Swift` globals directly

Repository: <https://github.com/RYF5584/frida-legacy-compat>

## Features

- Patches `frida.core.Session.create_script()` explicitly when enabled
- Detects legacy bridge scripts and compiles them on demand
- Installs the required bridge packages automatically
- No Node.js is required
- Selects a default bridge profile from `frida.__version__`

## Use Cases

This package is a good fit when:

- you already have a large Frida 16-style Python codebase
- your scripts still use `Java.perform(...)`, `ObjC`, or `Swift` globals
- you do not want to require Node.js on the end user's machine
- you want to keep the old Python call pattern on Frida 17+

This package is usually not needed when:

- you need support for `17.0 <= frida < 17.2`
- your project already uses ESM / TypeScript / a custom build pipeline
- you need fully validated `frida >= 18` support

## How It Works

Importing `frida_legacy_compat` alone does not patch anything.
You must call `frida_legacy_compat.patch_frida()` explicitly to
monkey-patch `frida.core.Session.create_script()`.

When the input source contains `Java.`, `ObjC.`, `Swift.`, or ESM
`import/export` syntax, the patch will:

1. create a temporary compile project in the local cache directory
2. resolve the default bridge profile from `frida.__version__`
3. install the matching bridge packages through `frida.PackageManager()`
4. generate an entrypoint that injects bridge globals into `globalThis`
5. build a bundle through `frida.Compiler()`
6. call the original `create_script()` with the compiled output

If the input is already a compiled Frida bundle, it is passed through directly.

## Installation

This package is published on PyPI and can be installed directly from:
<https://pypi.org/project/frida-legacy-compat/>

Recommended:

```bash
pip install frida-legacy-compat
```

Install together with `frida` if needed:

```bash
pip install 'frida-legacy-compat[full]'
```

Notes:

- This package does not restrict the installed `frida` version
- The recommended range is `frida>=17.2,<18`
- If the current `frida` version is unsupported, both `import frida_legacy_compat` and `frida_legacy_compat.patch_frida()` emit a localized warning instead of raising an error

With `uv`:

```bash
uv pip install frida-legacy-compat
```

Or directly:

```bash
uv add frida-legacy-compat
uv add 'frida-legacy-compat[full]'
```

## Compatibility

- `frida < 17`: installable; both `import` and `patch_frida()` only warn and remain a no-op
- `17.0 <= frida < 17.2`: installable; both `import` and `patch_frida()` only warn that `frida>=17.2,<18` is required
- `17.2 <= frida < 18`: supported
- `frida >= 18`: installable; both `import` and `patch_frida()` only warn that the version is outside the validated range

## Quick Start

```python
import frida
import frida_legacy_compat

frida_legacy_compat.patch_frida()

device = frida.get_usb_device()
session = device.attach("com.example.app")
source = """
Java.perform(function () {
  var Activity = Java.use("android.app.Activity");
  console.log(Activity);
});
"""

script = session.create_script(source)
script.load()
```

## What Changes For Users

If users already have:

```python
import frida
```

they usually only need to add:

```python
import frida_legacy_compat
```

Their existing `device.attach()`, `session.create_script()`, and `script.load()`
flow can usually stay unchanged.

## CLI

The package also provides a CLI:

```bash
frida-legacy -U -f com.example.app -l agent.js
```

## Optional Configuration

### Bridge version matrix
The package selects a default bridge profile automatically from
`frida.__version__`.
The currently built-in profile is:


- `frida-java-bridge@7.0.4`
- `frida-objc-bridge@8.0.5`
- `frida-swift-bridge@3.0.2`

At the moment, every supported version in `17.2 <= frida < 18` resolves to the
built-in `stable-17` profile.

If needed, you can still override the selection by:

- passing `patch_frida(bridge_profile="stable-17")`
- passing `patch_frida(bridges=[...])`
- setting `FRIDA_LEGACY_COMPAT_BRIDGE_PROFILE`

### Use environment variables with `auto_patch()`

```bash
export FRIDA_LEGACY_COMPAT_AUTO_PATCH=0
```

### Control compile policy

The default is `auto`, which only compiles when bridge globals or module syntax
are detected.

Supported values:

- `auto`
- `always`
- `never`

Example:

```bash
export FRIDA_LEGACY_COMPAT_COMPILE_POLICY=always
```

### Patch manually again

```python
import frida
import frida_legacy_compat

frida_legacy_compat.patch_frida()
```

### Select a bridge profile explicitly

```python
import frida
import frida_legacy_compat

frida_legacy_compat.patch_frida(bridge_profile="stable-17")
```

### Select a bridge profile from CLI

```bash
frida-legacy -U -n com.example.app -l agent.js --bridge-profile stable-17
```

## Notes

- The first injection may be slower because bridges are downloaded automatically
- The compatibility entrypoint is currently `Session.create_script()`
- Precompiled bundles are detected and passed through directly
- You can extend this later by patching `compile_script()` or adding cache
  cleanup helpers
