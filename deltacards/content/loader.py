import json
from importlib import import_module
from pathlib import Path

from deltacards.content.library import LIBRARY


CONTENT_MODULES = [
    # Cards
    'deltacards.content.cards.expansions.base.base',
    'deltacards.content.cards.expansions.base.common',
    'deltacards.content.cards.expansions.base.determination',
    'deltacards.content.cards.expansions.base.epic',
    'deltacards.content.cards.expansions.base.legendary',
    'deltacards.content.cards.expansions.base.rare',
    'deltacards.content.cards.expansions.base.token',
    'deltacards.content.cards.expansions.deltarune.base',
    'deltacards.content.cards.expansions.deltarune.common',
    'deltacards.content.cards.expansions.deltarune.determination',
    'deltacards.content.cards.expansions.deltarune.epic',
    'deltacards.content.cards.expansions.deltarune.legendary',
    'deltacards.content.cards.expansions.deltarune.rare',
    'deltacards.content.cards.expansions.deltarune.token',
    'deltacards.content.cards.expansions.uty.all',

    'deltacards.content.cards.souls.bravery',
    'deltacards.content.cards.souls.determination',
    'deltacards.content.cards.souls.integrity',
    'deltacards.content.cards.souls.justice',
    'deltacards.content.cards.souls.kindness',
    'deltacards.content.cards.souls.patience',
    'deltacards.content.cards.souls.perseverance',

    'deltacards.content.cards.tribes.amalgamates',
    'deltacards.content.cards.tribes.arachnids',
    'deltacards.content.cards.tribes.bargains',
    'deltacards.content.cards.tribes.chaos_weapons',
    'deltacards.content.cards.tribes.dances',
    'deltacards.content.cards.tribes.dogs',
    'deltacards.content.cards.tribes.froggits',
    'deltacards.content.cards.tribes.g_followers',
    'deltacards.content.cards.tribes.giga_attacks',
    'deltacards.content.cards.tribes.lost_souls',
    'deltacards.content.cards.tribes.molds',
    'deltacards.content.cards.tribes.packs',
    'deltacards.content.cards.tribes.pieces',
    'deltacards.content.cards.tribes.plants',
    'deltacards.content.cards.tribes.plugs',
    'deltacards.content.cards.tribes.rounds',
    'deltacards.content.cards.tribes.royal_guards',
    'deltacards.content.cards.tribes.snails',
    'deltacards.content.cards.tribes.temmies',
    'deltacards.content.cards.tribes.thrashing_parts',

    # Artifacts
    'deltacards.content.artifacts.base',
    'deltacards.content.artifacts.common',
    'deltacards.content.artifacts.legendary',
    'deltacards.content.artifacts.token',

    # Souls
    'deltacards.content.souls.standard',
]

CARDS_JSON = Path(__file__).resolve().parents[2] / 'AllCards.json'


def load():
    try:
        LIBRARY.get(1)
    except KeyError:
        pass
    else:
        return

    for name in CONTENT_MODULES:
        import_module(name)

    # TODO
    with open(CARDS_JSON) as f:
        data = json.load(f)
        if isinstance(data, dict):
            data = json.loads(data['cards'])
            with open(CARDS_JSON, 'w') as fw:
                json.dump(sorted(data, key=lambda x: x['id']), fw, indent=2)

    with open(CARDS_JSON) as f:
        LIBRARY.load_templates(json.load(f))
