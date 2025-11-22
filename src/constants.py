"""Constants used throughout the application."""

# Hook event name
HOOK_EVENT_NAME = "PreToolUse"

# Permission decision values
PERMISSION_ALLOW = "allow"
PERMISSION_DENY = "deny"
PERMISSION_ASK = "ask"

# Default permission decision values (default to deny for security)
DEFAULT_PERMISSION_DECISION = PERMISSION_DENY
DEFAULT_PERMISSION_REASON = "Invalid or missing permission decision from judgment system"
