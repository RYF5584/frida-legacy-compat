## Highlights

- Restores a Frida 16-style Python `session.create_script()` workflow on Frida 17+
- Keeps legacy plain JavaScript using `Java`, `ObjC`, and `Swift` globals working
- Avoids requiring Node.js on the end user's machine

## Included In This Release

- automatic `Session.create_script()` patching
- bridge profile selection based on `frida.__version__`
- CLI with `--doctor`
- GitHub and PyPI ready documentation

## Upgrade Notes

- `frida < 17` usually does not need this package
- `17.0 <= frida < 17.2` is not supported
- `17.2 <= frida < 18` is the current validated range
