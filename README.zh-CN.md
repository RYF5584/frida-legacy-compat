# frida-legacy-compat

[![Repository](https://img.shields.io/badge/GitHub-RYF5584%2Ffrida--legacy--compat-181717?logo=github)](https://github.com/RYF5584/frida-legacy-compat)
[![GitHub stars](https://img.shields.io/github/stars/RYF5584/frida-legacy-compat?style=social)](https://github.com/RYF5584/frida-legacy-compat/stargazers)

[简体中文](./README.zh-CN.md) | [English](./README.en.md)

`frida-legacy-compat` 是一个面向 Frida 17+ 的 Python 兼容层，用来把
Frida 16 风格的 `session.create_script()` 注入体验尽量恢复回来。

这个库就是专门用来解决 Frida 17.0.0 以上版本中，使用 Python API 执行旧版
JS 脚本时常见的 bridge 报错问题，例如：

```python
{'type': 'error', 'description': "ReferenceError: 'Java' is not defined", 'stack': "ReferenceError: 'Java' is not defined\n at (/script1.js:3)"}
```

Frida 17 以后，旧版 bridge 默认不再跟随原来的 plain JS 工作流一起可用，
很多场景需要改成 TypeScript/ESM 编译，或者额外下载 bridge，使用成本明显变高。

这个库的目标很直接：

- 安装一次
- 多加一行 `import frida_legacy_compat`
- 继续直接把旧版 JS 字符串传给 `session.create_script(source)`
- 旧脚本里的 `Java`、`ObjC`、`Swift` 继续可用

仓库地址：<https://github.com/RYF5584/frida-legacy-compat>

## 特性

- 安装后自动 patch `frida.core.Session.create_script()`
- 自动识别旧版 bridge 脚本并按需编译
- 自动安装所需 bridge 包
- 不需要 Node.js
- 根据 `frida.__version__` 自动选择默认 bridge profile

## 适用场景

适合以下场景：

- 已有大量 Frida 16 风格的 Python 注入代码
- JS 脚本仍然直接写 `Java.perform(...)`、`ObjC` 或 `Swift`
- 不希望要求最终用户安装 Node.js
- 希望在 Frida 17+ 环境下保留旧调用方式

不适合以下场景：

- 需要兼容 `17.0 <= frida < 17.2`
- 已经完全改成 ESM / TypeScript / 自定义打包流程
- 希望兼容 `frida >= 18` 但尚未完成验证

## 工作原理

导入 `frida_legacy_compat` 后，会自动 monkey patch
`frida.core.Session.create_script()`。

当检测到脚本里包含 `Java.`、`ObjC.`、`Swift.` 或 ESM `import/export`
语法时，补丁会：

1. 在本地缓存目录创建临时编译工程
2. 根据当前 `frida.__version__` 命中默认 bridge profile
3. 使用 `frida.PackageManager()` 安装对应 bridge
4. 生成入口文件并把 bridge 注入到 `globalThis`
5. 使用 `frida.Compiler()` 编译 bundle
6. 调回原始 `create_script()` 完成注入

如果传入内容本身已经是编译好的 Frida bundle，则会直接透传，不会重复编译。

## 安装

推荐安装方式：

```bash
pip install frida-legacy-compat
```

如果希望同时安装推荐范围内的 Frida：

```bash
pip install 'frida-legacy-compat[full]'
```

使用 `uv`：

```bash
uv pip install frida-legacy-compat
```

或者直接：

```bash
uv add frida-legacy-compat
uv add 'frida-legacy-compat[full]'
```

## 兼容性

- `frida < 17`：可安装、可保留 `import frida_legacy_compat`，导入后默认静默 no-op
- `17.0 <= frida < 17.2`：不支持
- `17.2 <= frida < 18`：支持
- `frida >= 18`：当前版本默认视为未验证

## 快速开始

```python
import frida
import frida_legacy_compat

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

## 用户需要改动什么

如果用户原本代码是：

```python
import frida
```

通常只需要额外加入：

```python
import frida_legacy_compat
```

其他 `device.attach()`、`session.create_script()`、`script.load()` 调用通常可以保持不变。

## CLI

命令行方式同样可用：

```bash
frida-legacy -U -f com.example.app -l agent.js
```

## 可选配置

### Bridge 版本矩阵

库会根据 `frida.__version__` 自动选择默认 bridge profile。

当前内置 profile 为：

- `frida-java-bridge@7.0.4`
- `frida-objc-bridge@8.0.5`
- `frida-swift-bridge@3.0.2`

当前 `17.2 <= frida < 18` 会命中内置的 `stable-17` profile。

如果需要手动覆盖，也可以：

- 直接传 `patch_frida(bridge_profile="stable-17")`
- 直接传 `patch_frida(bridges=[...])`
- 或设置环境变量 `FRIDA_LEGACY_COMPAT_BRIDGE_PROFILE`

### 关闭自动 patch

```bash
export FRIDA_LEGACY_COMPAT_AUTO_PATCH=0
```

### 控制编译策略

默认是 `auto`，只在检测到桥接全局或模块语法时自动编译。

可选值：

- `auto`
- `always`
- `never`

例如：

```bash
export FRIDA_LEGACY_COMPAT_COMPILE_POLICY=always
```

### 手动重新 patch

```python
import frida
import frida_legacy_compat

frida_legacy_compat.patch_frida()
```

### 指定 bridge profile

```python
import frida
import frida_legacy_compat

frida_legacy_compat.patch_frida(bridge_profile="stable-17")
```

### CLI 指定 bridge profile

```bash
frida-legacy -U -n com.example.app -l agent.js --bridge-profile stable-17
```

## 注意事项

- 第一次注入时会自动下载 bridge 包，所以会慢一点
- 当前兼容入口是 `Session.create_script()`
- 已编译 bundle 会被自动识别并直接透传
- 如果你后续还想做更强兼容，可以继续 patch `compile_script()` 等接口
