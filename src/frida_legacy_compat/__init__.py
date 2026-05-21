import warnings

from .compat import (
    CompatibilityError,
    ensure_runtime_compatibility,
    get_runtime_status,
    render_doctor_report,
    render_runtime_warning,
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

if _RUNTIME_STATUS.supported:
    auto_patch()
elif not _RUNTIME_STATUS.no_op:
    warnings.warn(render_runtime_warning(), RuntimeWarning, stacklevel=2)
