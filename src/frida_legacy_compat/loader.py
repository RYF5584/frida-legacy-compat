from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
from typing import Iterable, Sequence

from .compat import ensure_runtime_compatibility, parse_version

DEFAULT_BRIDGE_PROFILE = "stable-17"
BRIDGE_PROFILE_ENV = "FRIDA_LEGACY_COMPAT_BRIDGE_PROFILE"

BRIDGE_PROFILES = {
    "stable-17": (
        "frida-java-bridge@7.0.4",
        "frida-objc-bridge@8.0.5",
        "frida-swift-bridge@3.0.2",
    ),
}

BRIDGE_VERSION_MATRIX = (
    ((17, 2, 0), (18, 0, 0), "stable-17"),
)

DEFAULT_BRIDGES = BRIDGE_PROFILES[DEFAULT_BRIDGE_PROFILE]

TSCONFIG = {
    "compilerOptions": {
        "target": "es2020",
        "module": "esnext",
        "allowJs": True,
        "checkJs": False,
        "moduleResolution": "bundler",
        "skipLibCheck": True,
    },
    "include": ["./**/*"],
}


def _load_frida():
    ensure_runtime_compatibility()
    try:
        return importlib.import_module("frida")
    except ImportError as exc:
        raise RuntimeError(
            "frida is required. Install it with: pip install frida. "
            "Recommended supported range: frida>=17.2,<18"
        ) from exc


def _get_frida_version() -> str:
    frida = _load_frida()
    return getattr(frida, "__version__", "0.0.0")


def resolve_bridge_profile(
    frida_version: str | None = None,
    *,
    bridge_profile: str | None = None,
) -> str:
    profile = bridge_profile or os.getenv(BRIDGE_PROFILE_ENV, "").strip() or None
    if profile is not None:
        if profile not in BRIDGE_PROFILES:
            supported = ", ".join(sorted(BRIDGE_PROFILES))
            raise ValueError(f"unsupported bridge profile: {profile}; supported: {supported}")
        return profile

    parsed = parse_version(frida_version or _get_frida_version())
    for minimum, maximum, matched_profile in BRIDGE_VERSION_MATRIX:
        if minimum <= parsed < maximum:
            return matched_profile
    return DEFAULT_BRIDGE_PROFILE


def resolve_default_bridges(
    frida_version: str | None = None,
    *,
    bridge_profile: str | None = None,
) -> tuple[str, ...]:
    profile = resolve_bridge_profile(frida_version, bridge_profile=bridge_profile)
    return BRIDGE_PROFILES[profile]


def _normalize_bridge_specs(
    bridges: Iterable[str] | None,
    *,
    bridge_profile: str | None = None,
    frida_version: str | None = None,
) -> tuple[str, ...]:
    items = tuple(
        dict.fromkeys(
            bridges or resolve_default_bridges(frida_version, bridge_profile=bridge_profile)
        )
    )
    if not items:
        raise ValueError("at least one bridge package must be specified")
    return items


def _bridge_package_name(spec: str) -> str:
    return spec.split("@", 1)[0]


def _cache_root(cache_dir: str | os.PathLike[str] | None) -> Path:
    if cache_dir is not None:
        return Path(cache_dir).expanduser().resolve()
    return (Path.home() / ".cache" / "frida-legacy-compat").resolve()


def _project_id(source_name: str, source_text: str, bridges: Sequence[str]) -> str:
    fingerprint = json.dumps(
        {"name": source_name, "source": source_text, "bridges": list(bridges)},
        ensure_ascii=True,
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(fingerprint).hexdigest()[:16]


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_entrypoint(bridges: Sequence[str], source_name: str) -> str:
    lines = []
    exported_names = []
    for spec in bridges:
        package_name = _bridge_package_name(spec)
        if package_name == "frida-java-bridge":
            symbol = "Java"
        elif package_name == "frida-objc-bridge":
            symbol = "ObjC"
        elif package_name == "frida-swift-bridge":
            symbol = "Swift"
        else:
            symbol = package_name.replace("-", "_")
        lines.append(f'import {symbol} from "{package_name}";')
        exported_names.append(symbol)

    lines.append("")
    for symbol in exported_names:
        lines.append(f"(globalThis as any).{symbol} = {symbol};")

    lines.append("")
    # Use a dynamic import so the legacy globals are attached before the
    # user script executes. A static ESM import would evaluate the user script
    # first, which makes `Java` / `ObjC` / `Swift` unavailable at module load.
    lines.append(f'void import("./{source_name}");')
    lines.append("")
    return "\n".join(lines)


def _prepare_project(project_root: Path, source_name: str, source_text: str, bridges: Sequence[str]) -> Path:
    project_root.mkdir(parents=True, exist_ok=True)

    _write_json(
        project_root / "package.json",
        {
            "name": "frida-legacy-compat-cache",
            "private": True,
            "type": "module",
        },
    )
    _write_json(project_root / "tsconfig.json", TSCONFIG)

    # Ensure legacy plain JS can still be loaded through dynamic import().
    # Appending `export {}` marks the file as an ES module without changing
    # the runtime behavior of the original script body.
    module_source = f"{source_text.rstrip()}\n\nexport {{}};\n"
    (project_root / source_name).write_text(module_source, encoding="utf-8")
    entrypoint = project_root / "entrypoint.ts"
    entrypoint.write_text(_build_entrypoint(bridges, source_name), encoding="utf-8")
    return entrypoint


def ensure_bridges(
    project_root: str | os.PathLike[str],
    bridges: Iterable[str] | None = None,
    *,
    bridge_profile: str | None = None,
    progress: bool = False,
) -> tuple[str, ...]:
    frida = _load_frida()
    specs = _normalize_bridge_specs(bridges, bridge_profile=bridge_profile)
    root = Path(project_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    pm = frida.PackageManager()
    if progress:
        pm.on(
            "install-progress",
            lambda phase, fraction, details: print(
                {
                    "phase": phase,
                    "fraction": fraction,
                    "details": details,
                }
            ),
        )

    previous_cwd = Path.cwd()
    try:
        os.chdir(root)
        pm.install(specs=list(specs))
    finally:
        os.chdir(previous_cwd)

    return specs


def build_legacy_bundle(
    source: str,
    *,
    source_name: str = "user-script.js",
    cache_dir: str | os.PathLike[str] | None = None,
    bridges: Iterable[str] | None = None,
    bridge_profile: str | None = None,
    progress: bool = False,
) -> str:
    frida = _load_frida()
    specs = _normalize_bridge_specs(bridges, bridge_profile=bridge_profile)
    source_name = Path(source_name).name or "user-script.js"
    project_root = _cache_root(cache_dir) / _project_id(source_name, source, specs)
    entrypoint = _prepare_project(project_root, source_name, source, specs)
    ensure_bridges(project_root, specs, bridge_profile=bridge_profile, progress=progress)

    compiler = frida.Compiler()
    diagnostics: list[object] = []
    compiler.on("diagnostics", lambda diag: diagnostics.append(diag))

    try:
        return compiler.build(str(entrypoint), project_root=str(project_root))
    except Exception as exc:
        message = f"failed to compile legacy bundle: {exc}"
        if diagnostics:
            message = f"{message}; diagnostics={diagnostics!r}"
        raise RuntimeError(message) from exc


def build_legacy_bundle_from_file(
    script_path: str | os.PathLike[str],
    *,
    cache_dir: str | os.PathLike[str] | None = None,
    bridges: Iterable[str] | None = None,
    bridge_profile: str | None = None,
    progress: bool = False,
) -> str:
    path = Path(script_path).expanduser().resolve()
    source = path.read_text(encoding="utf-8")
    return build_legacy_bundle(
        source,
        source_name=path.name,
        cache_dir=cache_dir,
        bridges=bridges,
        bridge_profile=bridge_profile,
        progress=progress,
    )


def create_legacy_script(
    session,
    source: str,
    *,
    source_name: str = "user-script.js",
    cache_dir: str | os.PathLike[str] | None = None,
    bridges: Iterable[str] | None = None,
    bridge_profile: str | None = None,
    progress: bool = False,
    **create_script_kwargs,
):
    bundle = build_legacy_bundle(
        source,
        source_name=source_name,
        cache_dir=cache_dir,
        bridges=bridges,
        bridge_profile=bridge_profile,
        progress=progress,
    )
    return session.create_script(bundle, **create_script_kwargs)


def create_legacy_script_from_file(
    session,
    script_path: str | os.PathLike[str],
    *,
    cache_dir: str | os.PathLike[str] | None = None,
    bridges: Iterable[str] | None = None,
    bridge_profile: str | None = None,
    progress: bool = False,
    **create_script_kwargs,
):
    path = Path(script_path).expanduser().resolve()
    return create_legacy_script(
        session,
        path.read_text(encoding="utf-8"),
        source_name=path.name,
        cache_dir=cache_dir,
        bridges=bridges,
        bridge_profile=bridge_profile,
        progress=progress,
        **create_script_kwargs,
    )
