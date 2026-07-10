from typing import Any

from deltacards.actions.results import ActionResult, GoldSpentResult
from deltacards.model.cards import Card, Monster
from deltacards.model.entity import Entity
from deltacards.model.enums import Ability, CardKeyword, CardType, Expansion, PlayerId, Tribe
from deltacards.model.player import Player
from deltacards.model.snapshots import ArtifactSnapshot, CardSnapshot, EntitySnapshot, MonsterSnapshot, PlayerSnapshot, \
    SoulSnapshot
from deltacards.model.templates import CardTemplate, MonsterTemplate

_MISSING = object()


# -------------------------------
# Subject/template/card identity
# -------------------------------

def subject_of(entity: Any, default: Any = _MISSING) -> Any:
    if entity is None:
        return default

    if isinstance(entity, ActionResult):
        subject = entity.history_subject
        if subject is None:
            return default

        return subject

    return entity


def template_of(entity: Any, default: Any = _MISSING) -> CardTemplate | Any:
    entity = subject_of(entity, default=_MISSING)
    if entity is _MISSING:
        return default

    if isinstance(entity, (Card, CardSnapshot)):
        return entity.template

    if isinstance(entity, CardTemplate):
        return entity

    return default


def template_id_of(entity: Any, default: Any = _MISSING) -> int | Any:
    template = template_of(entity, default=_MISSING)
    if template is _MISSING:
        return default

    return template.id


def card_type_of(entity: Any, default: Any = _MISSING) -> CardType | Any:
    template = template_of(entity, default=_MISSING)
    if template is _MISSING:
        return default

    return template.type


def card_id_of(entity: Any, default: Any = _MISSING) -> int | Any:
    if entity is None:
        return default

    if isinstance(entity, (Card, CardSnapshot)):
        return entity.id

    if isinstance(entity, ActionResult):
        if entity.history_card_id is not None:
            return entity.history_card_id

    return default


def soul_id_of(entity: Any, default: Any = _MISSING) -> Any:
    template = template_of(entity, default=_MISSING)
    if template is _MISSING:
        return default

    return template.soul_id


# -----------------------------
# Controller/source/target ids
# -----------------------------

def controller_id_of(entity: Any, default: Any = _MISSING) -> PlayerId | Any:
    if entity is None:
        return default

    if isinstance(entity, ActionResult):
        subject = entity.history_subject
        if subject is not None:
            value = controller_id_of(subject, default=_MISSING)
            if value is not _MISSING:
                return value

        if entity.history_player_id is not None:
            return entity.history_player_id

        return default

    if isinstance(entity, (Player, PlayerSnapshot)):
        return entity.id

    if isinstance(entity, (Card, CardSnapshot, ArtifactSnapshot, SoulSnapshot)):
        return entity.controller_id

    return default


def source_id_of(entity: Any, default: Any = _MISSING) -> PlayerId | int | Any:
    if isinstance(entity, ActionResult):
        return entity.source_id

    return default


def target_id_of(entity: Any, default: Any = _MISSING) -> PlayerId | int | Any:
    if isinstance(entity, ActionResult):
        return entity.history_target_id if entity.history_target_id is not None else default

    if isinstance(entity, (Entity, EntitySnapshot)):
        return entity.id

    return default


def killer_id_of(entity: Any, default: Any = _MISSING) -> PlayerId | int | Any:
    if isinstance(entity, ActionResult):
        return entity.history_killer_id if entity.history_killer_id is not None else default

    return default


def attacker_id_of(entity: Any, default: Any = _MISSING) -> int | Any:
    if isinstance(entity, ActionResult):
        return entity.history_attacker_id if entity.history_attacker_id is not None else default

    return default


def defender_id_of(entity: Any, default: Any = _MISSING) -> PlayerId | int | Any:
    if isinstance(entity, ActionResult):
        return entity.history_defender_id if entity.history_defender_id is not None else default

    return default


# --------------------
# Entity values
# --------------------

def base_attr_of(entity: Any, attr: str, default: Any = _MISSING) -> Any:
    entity = subject_of(entity, default=_MISSING)
    if entity is _MISSING:
        return default

    if isinstance(entity, (Card, CardSnapshot)):
        if attr == 'cost':
            return entity.base.cost

        if not isinstance(entity, (Monster, MonsterSnapshot)):
            return default

        if attr == 'attack':
            return entity.base.attack

        if attr == 'hp':
            return entity.base.hp

        return default

    template = template_of(entity, default=_MISSING)
    if template is _MISSING:
        return default

    if attr == 'cost':
        return template.cost

    if not isinstance(template, MonsterTemplate):
        return default

    if attr == 'attack':
        return template.attack

    if attr == 'hp':
        return template.hp

    return default


def generated_of(entity: Any, default: Any = _MISSING) -> bool | Any:
    if entity is None:
        return default

    if isinstance(entity, GoldSpentResult):
        return entity.is_generated

    if isinstance(entity, ActionResult):
        subject = entity.history_subject
        if subject is None:
            return default

        return generated_of(subject, default=default)

    if isinstance(entity, (Card, CardSnapshot)):
        return entity.is_generated

    if isinstance(entity, CardTemplate):
        return False

    return default


def has_keyword(entity: Any, keyword: CardKeyword, default: bool = False) -> bool:
    entity = subject_of(entity, default=_MISSING)
    if entity is _MISSING:
        return default

    if isinstance(entity, (Card, CardTemplate, CardSnapshot)):
        return entity.has_keyword(keyword)

    return default


def status_of(entity: Any, status_id: Any, default: int = 0) -> int:
    entity = subject_of(entity, default=_MISSING)
    if entity is _MISSING:
        return default

    if isinstance(entity, (Card, CardTemplate, CardSnapshot)):
        return entity.get_status(status_id)

    return default


def has_ability(entity: Any, ability: Ability, default: bool = False) -> bool:
    entity = subject_of(entity, default=_MISSING)
    if entity is _MISSING:
        return default

    return entity.has_ability(ability)


def tribes_of(entity: Any, default: Any = _MISSING) -> tuple[Tribe] | Any:
    entity = subject_of(entity, default=_MISSING)
    if entity is _MISSING:
        return default

    if isinstance(entity, Card):
        return entity.tribes

    template = template_of(entity, default=_MISSING)
    if isinstance(template, CardTemplate):
        return template.tribes

    return default


def has_tribe(entity: Any, tribe: Tribe, default: bool = False) -> bool:
    tribes = tribes_of(entity, default=_MISSING)
    if tribes is _MISSING:
        return default

    if tribe is Tribe.ALL:
        return Tribe.ALL in tribes

    return (tribe in tribes) or (Tribe.ALL in tribes)


def expansion_of(entity: Any, default: Any = _MISSING) -> Expansion | Any:
    template = template_of(entity, default=_MISSING)
    if template is _MISSING:
        return default

    return template.expansion


def _template_attr(entity: Any, attr: str, default: Any = _MISSING) -> Any:
    template = template_of(entity, default=_MISSING)
    if template is _MISSING:
        return default

    try:
        return getattr(template, attr)
    except AttributeError:
        return default


_SPECIAL_ATTR_GETTERS = {
    'template_id': template_id_of,

    'card_id': card_id_of,
    'monster_id': card_id_of,

    'card_type': card_type_of,
    'type': card_type_of,

    'controller_id': controller_id_of,
    'source_id': source_id_of,
    'target_id': target_id_of,
    'killer_id': killer_id_of,
    'attacker_id': attacker_id_of,
    'defender_id': defender_id_of,

    'is_generated': generated_of,
    'tribes': tribes_of,
}


def attr_of(entity: Any, attr: str, default: Any = _MISSING) -> Any:
    """Common attribute getter for DSL values"""
    if entity is None:
        return default

    if isinstance(entity, ActionResult):
        # Prioritize using fields on `ActionResult` over subject/template fields.
        try:
            return getattr(entity, attr)
        except AttributeError:
            pass

        getter = _SPECIAL_ATTR_GETTERS.get(attr)
        if getter is not None:
            value = getter(entity, default=_MISSING)
            if value is not _MISSING:
                return value

        subject = entity.history_subject
        if subject is not None:
            return attr_of(subject, attr, default=default)

        return default

    getter = _SPECIAL_ATTR_GETTERS.get(attr)
    if getter is not None:
        value = getter(entity, default=_MISSING)
        if value is not _MISSING:
            return value

    try:
        return getattr(entity, attr)
    except AttributeError:
        pass

    # Example: `CardSnapshot` doesn't have `name`, but its template does.
    value = _template_attr(entity, attr, default=_MISSING)
    if value is not _MISSING:
        return value

    return default
