# frida-legacy-compat

[![Repository](https://img.shields.io/badge/GitHub-RYF5584%2Ffrida--legacy--compat-181717?logo=github)](https://github.com/RYF5584/frida-legacy-compat)
[![GitHub stars](https://img.shields.io/github/stars/RYF5584/frida-legacy-compat?style=social)](https://github.com/RYF5584/frida-legacy-compat/stargazers)

[默认中文](./README.md) | [English](./README.en.md)

`frida-legacy-compat` 是一个面向 Frida 17+ 的 Python 兼容层，用来把 Frida 16 风格的 `session.create_script()` 注入体验尽量恢复回来。

这个库就是专门用来解决 Frida 17.0.0 以上版本中，使用 Python API 执行旧版 JS 脚本时常见的 bridge 报错问题，例如：

```python
{'type': 'error', 'description': "ReferenceError: 'Java' is not defined", 'stack': "ReferenceError: 'Java' is not defined\n at (/script1.js:3)"}
```

Frida 17 以后，旧版 bridge 默认不再跟随原来的 plain JS 工作流一起可用，很多场景需要改成 TypeScript/ESM 编译，或者额外下载 bridge，使用成本明显变高。

这个库的目标很直接：

- 安装一次
- 多加一行 `import frida_legacy_compat`
- 显式调用 `frida_legacy_compat.patch_frida()`
- 继续直接把旧版 JS 字符串传给 `session.create_script(source)`
- 旧脚本里的 `Java`、`ObjC`、`Swift` 继续可用

仓库地址：<https://github.com/RYF5584/frida-legacy-compat>

## 特性

- 显式调用后 patch `frida.core.Session.create_script()`
- 自动识别旧版 bridge 脚本并按需编译
- 自动安装所需 bridge 包
- 不需要 Node.js
- 根据 `frida.__version__` 自动选择默认 bridge profile

## 安装

本项目已发布到 PyPI，可直接通过 PyPI 安装：
<https://pypi.org/project/frida-legacy-compat/>

```bash
pip install frida-legacy-compat
```

如果希望同时安装 `frida`：

```bash
pip install 'frida-legacy-compat[full]'
```

说明：

- 本库安装时不限制 `frida` 版本
- 推荐范围为 `frida>=17.2,<18`
- 如果当前 `frida` 版本不满足，`import frida_legacy_compat` 和 `frida_legacy_compat.patch_frida()` 都只会给出中英文 warning，不会报错

使用 `uv add`：

```bash
uv add frida-legacy-compat
uv add 'frida-legacy-compat[full]'
```

## 兼容性

- `frida < 17`：可安装；`import` 和 `patch_frida()` 都只会 warning，并保持 no-op
- `17.0 <= frida < 17.2`：可安装；`import` 和 `patch_frida()` 都只会 warning，提示需要 `frida>=17.2,<18`
- `17.2 <= frida < 18`：支持
- `frida >= 18`：可安装；`import` 和 `patch_frida()` 都只会 warning，提示当前不在已验证范围内

## 快速开始

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

## CLI

```bash
frida-legacy -U -f com.example.app -l agent.js
```

## 文档

- [English documentation](./README.en.md)
- [更新日志](./CHANGELOG.md)
- [安全策略](./SECURITY.md)
- [v1.1.0 发布说明](./docs/releases/v1.1.0.md)
- [GitHub 仓库](https://github.com/RYF5584/frida-legacy-compat)

## 注意事项

- 第一次运行可能会慢一点，因为 bridge 包会按需安装
- 已编译的 Frida bundle 会被自动识别并直接透传
- 当前兼容入口是 `Session.create_script()`
