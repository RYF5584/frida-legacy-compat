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
            "- 本库安装时不限制 frida 版本\n"
            "- 推荐可用范围: frida>=17.2,<18\n"
            "- 如果当前 frida 版本不满足，导入时会自动给出中英文 warning 提示\n"
            "- 如需同时安装 frida，可使用: pip install 'frida-legacy-compat[full]'\n"
        )
    else:
        message = (
            "\n[frida-legacy-compat] Install note:\n"
            "- This package does not restrict the installed frida version\n"
            "- Recommended supported range: frida>=17.2,<18\n"
            "- If the current frida version is unsupported, importing will emit a localized warning\n"
            "- To install this package together with frida, use: pip install 'frida-legacy-compat[full]'\n"
        )
    print(message)


_emit_install_hint()

setup()
