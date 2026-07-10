import json
from importlib import import_module
from pathlib import Path

from deltacards.content.library import LIBRARY

CONTENT_MODULES = [
    # Cards
    'deltacards.content.cards.rarities.base',
    'deltacards.content.cards.rarities.token',
    'deltacards.content.cards.souls.patience',

    # Artifacts
    'deltacards.content.artifacts.base',
    'deltacards.content.artifacts.common',
    'deltacards.content.artifacts.legendary',
    'deltacards.content.artifacts.token',

    # Souls
    'deltacards.content.souls.standard',
]

CARDS_JSON = Path(__file__).resolve().parents[2] / 'cards.json'


def load():
    try:
        LIBRARY.get(1)
    except KeyError:
        pass
    else:
        return

    with open(CARDS_JSON) as f:
        LIBRARY.load_templates(json.load(f))

    for name in CONTENT_MODULES:
        import_module(name)
