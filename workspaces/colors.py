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

WORKPLACE_COLOR_HEX = {
    "teal": "#0d9488",
    "sky": "#0284c7",
    "violet": "#7c3aed",
    "amber": "#d97706",
    "rose": "#e11d48",
    "lime": "#65a30d",
    "indigo": "#4f46e5",
    "orange": "#ea580c",
}


def workplace_color_key(workplace_id):
    if not workplace_id:
        return WORKPLACE_COLOR_KEYS[0]
    return WORKPLACE_COLOR_KEYS[workplace_id % len(WORKPLACE_COLOR_KEYS)]


def workplace_color_hex(workplace_id):
    return WORKPLACE_COLOR_HEX[workplace_color_key(workplace_id)]
