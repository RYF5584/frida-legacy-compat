from .compat import (
    CompatibilityError,
    ensure_runtime_compatibility,
    get_runtime_status,
    render_doctor_report,
    render_runtime_warning,
    warn_runtime_status,
)
from .loader import (
    BRIDGE_PROFILE_ENV,
    BRIDGE_PROFILES,
    DEFAULT_BRIDGES,
    DEFAULT_BRIDGE_PROFILE,
    build_legacy_bundle,
    build_legacy_bundle_from_file,
    create_legacy_script,
    create_legacy_script_from_file,
    ensure_bridges,
    resolve_bridge_profile,
    resolve_default_bridges,
)
from .patch import auto_patch, is_patched, patch_frida, patch_state, unpatch_frida

# Re-export selected compatibility helpers as part of the public API.
render_runtime_warning = render_runtime_warning

__all__ = [
    "CompatibilityError",
    "BRIDGE_PROFILE_ENV",
    "BRIDGE_PROFILES",
    "DEFAULT_BRIDGES",
    "DEFAULT_BRIDGE_PROFILE",
    "build_legacy_bundle",
    "build_legacy_bundle_from_file",
    "create_legacy_script",
    "create_legacy_script_from_file",
    "ensure_bridges",
    "resolve_bridge_profile",
    "resolve_default_bridges",
    "ensure_runtime_compatibility",
    "get_runtime_status",
    "render_doctor_report",
    "auto_patch",
    "patch_frida",
    "unpatch_frida",
    "is_patched",
    "patch_state",
]

_RUNTIME_STATUS = get_runtime_status()

if not _RUNTIME_STATUS.supported:
    warn_runtime_status(stacklevel=2)
