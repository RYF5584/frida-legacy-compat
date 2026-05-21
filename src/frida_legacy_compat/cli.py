from __future__ import annotations

import argparse
from pathlib import Path

from .compat import CompatibilityError, ensure_runtime_compatibility
from .loader import create_legacy_script_from_file


def _message_printer(message, data):
    print(message)
    if data:
        print(f"[binary data] {len(data)} bytes")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="frida-legacy",
        description="Load a legacy plain JS Frida script through the Frida 17 compiler",
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("-f", "--spawn", metavar="APP", help="spawn and attach to an application")
    target.add_argument("-n", "--attach-name", metavar="NAME", help="attach to a process by name")
    target.add_argument("-p", "--attach-pid", metavar="PID", type=int, help="attach to a process by pid")

    device = parser.add_mutually_exclusive_group()
    device.add_argument("-U", "--usb", action="store_true", help="use the first USB device")
    device.add_argument("-D", "--device-id", help="attach to a device by id")
    device.add_argument("-H", "--host", help="attach to a remote frida-server host[:port]")

    parser.add_argument("-l", "--load", required=True, help="path to the legacy .js script")
    parser.add_argument("--cache-dir", help="cache directory used for compiled projects")
    parser.add_argument("--bridge-profile", help="bridge profile selected from the built-in version matrix")
    parser.add_argument(
        "--bridge",
        dest="bridges",
        action="append",
        help="bridge package to install; may be specified multiple times",
    )
    parser.add_argument(
        "--pause",
        action="store_true",
        help="do not resume the spawned process after the script is loaded",
    )
    return parser


def _get_device(frida, args):
    if args.device_id:
        return frida.get_device(args.device_id)
    if args.host:
        return frida.get_device_manager().add_remote_device(args.host)
    if args.usb:
        return frida.get_usb_device()
    return frida.get_local_device()


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        import frida
    except ImportError as exc:
        raise SystemExit("frida is required. Install it with: pip install 'frida>=17.2,<18'") from exc

    try:
        ensure_runtime_compatibility()
    except CompatibilityError as exc:
        raise SystemExit(str(exc)) from exc

    device = _get_device(frida, args)
    script_path = Path(args.load).expanduser().resolve()

    spawned_pid = None
    if args.spawn:
        spawned_pid = device.spawn([args.spawn])
        session = device.attach(spawned_pid)
    elif args.attach_name:
        session = device.attach(args.attach_name)
    else:
        session = device.attach(args.attach_pid)

    script = create_legacy_script_from_file(
        session,
        script_path,
        cache_dir=args.cache_dir,
        bridges=args.bridges,
        bridge_profile=args.bridge_profile,
    )
    script.on("message", _message_printer)
    script.load()

    if spawned_pid is not None and not args.pause:
        device.resume(spawned_pid)

    try:
        input("Press Enter to detach...\n")
    finally:
        session.detach()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
