from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional

from .compat import get_runtime_status
from .loader import build_legacy_bundle

BUNDLE_PREFIX = "📦"
BUNDLE_SEPARATOR = "\n✄\n"
AUTO_PATCH_ENV = "FRIDA_LEGACY_COMPAT_AUTO_PATCH"
COMPILE_POLICY_ENV = "FRIDA_LEGACY_COMPAT_COMPILE_POLICY"
DEFAULT_COMPILE_POLICY = "auto"
SUPPORTED_POLICIES = {"auto", "always", "never"}

_PATCH_STATE = {
    "enabled": False,
    "original": None,
    "cache_dir": None,
    "bridges": None,
    "bridge_profile": None,
    "progress": False,
    "policy": DEFAULT_COMPILE_POLICY,
}

_BRIDGE_GLOBAL_RE = re.compile(r"\b(?:Java|ObjC|Swift)\s*\.")
_ESM_RE = re.compile(r"(^|\n)\s*(?:import|export)\s", re.MULTILINE)


def _load_frida():
    import frida

    return frida


def _is_compiled_bundle(source: str) -> bool:
    stripped = source.lstrip()
    return stripped.startswith(BUNDLE_PREFIX) or BUNDLE_SEPARATOR in source[:4096]


def _looks_like_module(name: str | None, source: str) -> bool:
    if name is not None:
        suffix = Path(name).suffix.lower()
        if suffix in {".ts", ".tsx", ".mts", ".cts"}:
            return True
    return bool(_ESM_RE.search(source))


def _should_compile_source(
    source: str,
    *,
    name: str | None = None,
    snapshot: Optional[bytes],
    policy: str,
) -> bool:
    if snapshot is not None:
        return False
    if policy == "never":
        return False
    if _is_compiled_bundle(source):
        return False
    if policy == "always":
        return True
    if _looks_like_module(name, source):
        return True
    return bool(_BRIDGE_GLOBAL_RE.search(source))


def _patched_create_script(
    self,
    source: str,
    name: str | None = None,
    snapshot: bytes | None = None,
    runtime: str | None = None,
):
    original = _PATCH_STATE["original"]
    if original is None:
        raise RuntimeError("frida legacy compat patch is not initialized")

    if _should_compile_source(
        source,
        name=name,
        snapshot=snapshot,
        policy=_PATCH_STATE["policy"],
    ):
        source_name = Path(name).name if name else "user-script.js"
        bundle = build_legacy_bundle(
            source,
            source_name=source_name,
            cache_dir=_PATCH_STATE["cache_dir"],
            bridges=_PATCH_STATE["bridges"],
            bridge_profile=_PATCH_STATE["bridge_profile"],
            progress=bool(_PATCH_STATE["progress"]),
        )
        return original(self, bundle, name=name, snapshot=snapshot, runtime=runtime)

    return original(self, source, name=name, snapshot=snapshot, runtime=runtime)


def patch_frida(
    *,
    cache_dir: str | None = None,
    bridges: tuple[str, ...] | list[str] | None = None,
    bridge_profile: str | None = None,
    progress: bool = False,
    compile_policy: str | None = None,
):
    status = get_runtime_status()
    if status.no_op:
        return _load_frida()
    if not status.supported:
        from .compat import CompatibilityError, render_doctor_report

        raise CompatibilityError(render_doctor_report())
    frida = _load_frida()
    policy = (compile_policy or os.getenv(COMPILE_POLICY_ENV, DEFAULT_COMPILE_POLICY)).lower()
    if policy not in SUPPORTED_POLICIES:
        raise ValueError(f"unsupported compile policy: {policy}")

    session_cls = frida.core.Session
    if not _PATCH_STATE["enabled"]:
        _PATCH_STATE["original"] = session_cls.create_script
        session_cls.create_script = _patched_create_script
        _PATCH_STATE["enabled"] = True

    _PATCH_STATE["cache_dir"] = cache_dir
    _PATCH_STATE["bridges"] = tuple(bridges) if bridges is not None else None
    _PATCH_STATE["bridge_profile"] = bridge_profile
    _PATCH_STATE["progress"] = progress
    _PATCH_STATE["policy"] = policy
    return frida


def unpatch_frida():
    if not _PATCH_STATE["enabled"]:
        return

    frida = _load_frida()
    frida.core.Session.create_script = _PATCH_STATE["original"]
    _PATCH_STATE["enabled"] = False


def is_patched() -> bool:
    return bool(_PATCH_STATE["enabled"])


def patch_state() -> dict[str, Any]:
    return dict(_PATCH_STATE)


def auto_patch():
    value = os.getenv(AUTO_PATCH_ENV, "1").strip().lower()
    if value not in {"0", "false", "no", "off"}:
        patch_frida()
