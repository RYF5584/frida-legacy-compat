from __future__ import annotations

import locale
import os
from dataclasses import dataclass
from typing import Optional


SUPPORTED_MIN_VERSION = (17, 2, 0)
SUPPORTED_MAX_VERSION = (18, 0, 0)


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
                "推荐：`pip install 'frida>=17.2,<18'` 或 `pip install 'frida-legacy-compat[full]'`"
            ),
            "en": (
                "Frida Python bindings are not installed.\n"
                "Please install `frida` first.\n"
                "Recommended: `pip install 'frida>=17.2,<18'` or `pip install 'frida-legacy-compat[full]'`"
            ),
        },
        "unnecessary_pre17": {
            "zh-CN": (
                f"检测到 frida 版本为 {version_text}。\n"
                "Frida 17 以下默认自带 Java/ObjC/Swift bridge，通常不需要安装 `frida-legacy-compat`。\n"
                "建议：直接使用当前 frida，或卸载本库。"
            ),
            "en": (
                f"Detected frida version: {version_text}.\n"
                "Frida versions below 17 already bundle the Java/ObjC/Swift bridges, so `frida-legacy-compat` is usually unnecessary.\n"
                "Recommendation: use your current frida directly, or uninstall this package."
            ),
        },
        "unsupported_17_0_to_17_1": {
            "zh-CN": (
                f"检测到 frida 版本为 {version_text}。\n"
                "`frida-legacy-compat` 仅支持 Frida 17.2+。\n"
                "请升级到 `frida>=17.2,<18` 后再使用。"
            ),
            "en": (
                f"Detected frida version: {version_text}.\n"
                "`frida-legacy-compat` supports Frida 17.2+ only.\n"
                "Please upgrade to `frida>=17.2,<18` before using this package."
            ),
        },
        "unsupported_ge18": {
            "zh-CN": (
                f"检测到 frida 版本为 {version_text}。\n"
                "当前版本的 `frida-legacy-compat` 只验证了 Frida 17.2.x 到 17.x。\n"
                "如需继续使用，请等待对 Frida 18+ 的兼容验证或自行覆盖兼容策略。"
            ),
            "en": (
                f"Detected frida version: {version_text}.\n"
                "This release of `frida-legacy-compat` has only been validated against Frida 17.2.x through 17.x.\n"
                "Please wait for Frida 18+ compatibility support or override the policy yourself."
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
