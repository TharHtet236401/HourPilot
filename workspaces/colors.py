WORKPLACE_COLOR_KEYS = (
    "teal",
    "sky",
    "violet",
    "amber",
    "rose",
    "lime",
    "indigo",
    "orange",
)


def workplace_color_key(workplace_id):
    if not workplace_id:
        return WORKPLACE_COLOR_KEYS[0]
    return WORKPLACE_COLOR_KEYS[workplace_id % len(WORKPLACE_COLOR_KEYS)]
