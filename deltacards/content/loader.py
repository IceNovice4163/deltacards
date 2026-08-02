from importlib import import_module
from pathlib import Path

from deltacards.content.card_data import load_or_build_cards
from deltacards.content.library import LIBRARY
from deltacards.model.cards import cards


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

    # Enchantments
    'deltacards.content.enchantments.standard',

    # Artifacts
    'deltacards.content.artifacts.base',
    'deltacards.content.artifacts.common',
    'deltacards.content.artifacts.legendary',
    'deltacards.content.artifacts.quests',
    'deltacards.content.artifacts.token',

    # Souls
    'deltacards.content.souls.standard',
]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_CARDS_JSON = PROJECT_ROOT / 'AllCards.json'
CACHE_CARDS_JSON = PROJECT_ROOT / 'data' / 'cards.json'


def load_templates(*, force_rebuild: bool = False) -> None:
    LIBRARY.load_templates(
        load_or_build_cards(
            source_path=SOURCE_CARDS_JSON,
            cache_path=CACHE_CARDS_JSON,
            abilities_by_card={
                card_id: card_cls.declared_ability_names()
                for card_id, card_cls in cards.items()
            },
            force_rebuild=force_rebuild,
        )
    )


def load(*, force_rebuild: bool = False) -> None:
    for module_name in CONTENT_MODULES:
        import_module(module_name)

    load_templates(force_rebuild=force_rebuild)
