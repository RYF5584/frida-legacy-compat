from __future__ import annotations

import locale
import os
import warnings
from dataclasses import dataclass
from typing import Optional


SUPPORTED_MIN_VERSION = (17, 2, 0)
SUPPORTED_MAX_VERSION = (18, 0, 0)
_EMITTED_WARNINGS: set[tuple[str, str, Optional[str]]] = set()


class CompatibilityError(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimeStatus:
    status: str
    language: str
    frida_version: Optional[str]

    @property
    def supported(self) -> bool:
        return self.status == "supported"

    @property
    def no_op(self) -> bool:
        return self.status == "unnecessary_pre17"


def _detect_language() -> str:
    for key in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.getenv(key)
        if value:
            return "zh-CN" if value.lower().startswith("zh") else "en"

    try:
        current = locale.getlocale()[0]
    except Exception:
        current = None
    if current:
        return "zh-CN" if current.lower().startswith("zh") else "en"

    return "en"


def parse_version(version: str) -> tuple[int, int, int]:
    parts = []
    current = ""
    for char in version:
        if char.isdigit():
            current += char
        elif current:
            parts.append(int(current))
            current = ""
            if len(parts) >= 3:
                break
    if current and len(parts) < 3:
        parts.append(int(current))
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def _message(language: str, key: str, *, version: Optional[str]) -> str:
    version_text = version or "unknown"
    messages = {
        "missing": {
            "zh-CN": (
                "未检测到 frida Python 绑定。\n"
                "请先安装 `frida`。\n"
                "推荐可用范围：`frida>=17.2,<18`。\n"
                "可使用：`pip install frida` 或 `pip install 'frida-legacy-compat[full]'`"
            ),
            "en": (
                "Frida Python bindings are not installed.\n"
                "Please install `frida` first.\n"
                "Recommended supported range: `frida>=17.2,<18`.\n"
                "You can use: `pip install frida` or `pip install 'frida-legacy-compat[full]'`"
            ),
        },
        "unnecessary_pre17": {
            "zh-CN": (
                f"检测到 frida 版本为 {version_text}。\n"
                "当前版本不在 `frida-legacy-compat` 的推荐范围内。\n"
                "推荐范围为 `frida>=17.2,<18`。\n"
                "Frida 17 以下通常不需要本库，导入后会保持 no-op。"
            ),
            "en": (
                f"Detected frida version: {version_text}.\n"
                "This version is outside the recommended range for `frida-legacy-compat`.\n"
                "Recommended range: `frida>=17.2,<18`.\n"
                "Frida versions below 17 usually do not need this package, and importing will remain a no-op."
            ),
        },
        "unsupported_17_0_to_17_1": {
            "zh-CN": (
                f"检测到 frida 版本为 {version_text}。\n"
                "当前版本不在支持范围内。\n"
                "请使用 `frida>=17.2,<18`。"
            ),
            "en": (
                f"Detected frida version: {version_text}.\n"
                "This version is outside the supported range.\n"
                "Please use `frida>=17.2,<18`."
            ),
        },
        "unsupported_ge18": {
            "zh-CN": (
                f"检测到 frida 版本为 {version_text}。\n"
                "当前版本不在已验证范围内。\n"
                "推荐范围为 `frida>=17.2,<18`。\n"
                "如需继续使用，请等待 Frida 18+ 兼容验证。"
            ),
            "en": (
                f"Detected frida version: {version_text}.\n"
                "This version is outside the validated range.\n"
                "Recommended range: `frida>=17.2,<18`.\n"
                "Please wait for Frida 18+ compatibility validation before using it."
            ),
        },
        "supported": {
            "zh-CN": f"当前 frida 版本 {version_text} 受支持，可启用 `frida-legacy-compat`。",
            "en": f"Current frida version {version_text} is supported and can use `frida-legacy-compat`.",
        },
    }
    return messages[key][language]


def get_runtime_status() -> RuntimeStatus:
    language = _detect_language()
    try:
        import frida
    except ImportError:
        return RuntimeStatus(status="missing", language=language, frida_version=None)

    version = getattr(frida, "__version__", "0.0.0")
    parsed = parse_version(version)

    if parsed < (17, 0, 0):
        return RuntimeStatus(status="unnecessary_pre17", language=language, frida_version=version)
    if parsed < SUPPORTED_MIN_VERSION:
        return RuntimeStatus(status="unsupported_17_0_to_17_1", language=language, frida_version=version)
    if parsed >= SUPPORTED_MAX_VERSION:
        return RuntimeStatus(status="unsupported_ge18", language=language, frida_version=version)
    return RuntimeStatus(status="supported", language=language, frida_version=version)


def ensure_runtime_compatibility() -> RuntimeStatus:
    status = get_runtime_status()
    if not status.supported and not status.no_op:
        raise CompatibilityError(_message(status.language, status.status, version=status.frida_version))
    return status


def render_doctor_report() -> str:
    status = get_runtime_status()
    head = {
        "zh-CN": "frida-legacy-compat 环境检查",
        "en": "frida-legacy-compat environment check",
    }[status.language]
    body = _message(status.language, status.status, version=status.frida_version)
    return f"{head}\nstatus: {status.status}\n\n{body}"


def render_runtime_warning() -> str:
    status = get_runtime_status()
    return _message(status.language, status.status, version=status.frida_version)


def warn_runtime_status(*, stacklevel: int = 2) -> None:
    status = get_runtime_status()
    if status.supported:
        return
    key = (status.status, status.language, status.frida_version)
    if key in _EMITTED_WARNINGS:
        return
    _EMITTED_WARNINGS.add(key)
    warnings.warn(
        _message(status.language, status.status, version=status.frida_version),
        RuntimeWarning,
        stacklevel=stacklevel,
    )
