"""Student extension: content-level injection defenses.

Budget and confirmation policies must keep working even if this module
never flags the SonicMax hidden text. Students add labeling and schema
checks here without weakening the backend money rules.
"""


def looks_like_instruction(text: str) -> bool:
    # TODO(STUDENT): Heuristic detection of seller text that tries to override
    # the customer task (ignore budget, add N units, skip confirmation).
    return False


def wrap_untrusted(label: str, text: str) -> str:
    # TODO(STUDENT): Return a labeled envelope so the model (and X-Ray) can
    # tell developer instructions apart from seller copy.
    return text
