"""
CPY052 — REMOVED (wrong detector)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This rule was removed because threading.local() itself is not a
compatibility problem. The rule's description about GIL-protected
atomicity was misleading — threading.local is per-thread, not shared.
"""
# Deprecated — rule removed. Kept for ID reservation.
