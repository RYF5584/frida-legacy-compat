from __future__ import annotations

import locale
import os

from setuptools import setup


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


def _emit_install_hint() -> None:
    language = _detect_language()
    if language == "zh-CN":
        message = (
            "\n[frida-legacy-compat] 安装提示:\n"
            "- frida < 17: 本库可安装，但导入后默认静默 no-op\n"
            "- 17.0 <= frida < 17.2: 当前暂不支持，导入时会提示升级到 frida>=17.2,<18\n"
            "- 17.2 <= frida < 18: 当前支持范围\n"
            "- 如需同时安装推荐版本，可使用: pip install 'frida-legacy-compat[full]'\n"
        )
    else:
        message = (
            "\n[frida-legacy-compat] Install note:\n"
            "- frida < 17: installable, but import defaults to a silent no-op\n"
            "- 17.0 <= frida < 17.2: currently unsupported; importing will warn and ask for frida>=17.2,<18\n"
            "- 17.2 <= frida < 18: supported range\n"
            "- To install with the recommended Frida range: pip install 'frida-legacy-compat[full]'\n"
        )
    print(message)


_emit_install_hint()

setup()
