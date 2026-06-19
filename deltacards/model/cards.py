from dataclasses import asdict, dataclass, replace
from typing import Generic, TypeVar

from deltacards.content.library import LIBRARY
from deltacards.model.entity import Entity
from deltacards.model.enums import (
    Ability,
    CardKeyword,
    CardRarity,
    CardStatusId,
    CardType,
    CardZone,
    PlayerId,
    Tribe,
)
from deltacards.model.snapshots import CardSnapshot, MonsterSnapshot, SpellSnapshot
from deltacards.model.templates import CardTemplate, MonsterTemplate

TTemplate = TypeVar('TTemplate', bound=CardTemplate)

cards = {}


def card(card_id: int):
    def wrapper(class_):
        if card_id in cards:
            raise ValueError(f"Card with ID {card_id} already exists")

        cards[card_id] = class_
        return class_

    return wrapper


@dataclass(frozen=True, slots=True)
class BaseStats:
    cost: int
    attack: int | None = None
    hp: int | None = None

    def serialize(self) -> dict:
        return {
            'cost': self.cost,
            'attack': self.attack,
            'hp': self.hp,
        }


@dataclass(slots=True)
class CardBuffs:
    cost: int = 0
    attack: int = 0
    max_hp: int = 0

    def serialize(self) -> dict:
        return {
            'cost': self.cost,
            'attack': self.attack,
            'max_hp': self.max_hp,
        }


@dataclass(frozen=True, slots=True)
class CaughtCardData:
    template_id: int
    controller_id: PlayerId

    def serialize(self) -> dict:
        return {
            'template_id': self.template_id,
            'controller_id': self.controller_id.value,
        }


class Card(Entity, Generic[TTemplate]):
    targets = None

    def __init__(
        self,
        id: int,
        template: TTemplate,
        controller_id: PlayerId,
        zone: CardZone = CardZone.INVALID,
        creator_id: int | None = None,
        creator_base_identity: tuple[str, int] | None = None,
        base: BaseStats | None = None,
    ):
        super().__init__(id)

        self.template = template
        self.owner_id = controller_id
        self.controller_id = controller_id
        self._zone = zone
        self.creator_id = creator_id
        self.creator_base_identity = creator_base_identity
        self._base = base

        self.keywords = self.template.keywords
        self.statuses = self.template.statuses.copy()

        self.buffs = CardBuffs()
        self.caught_card: CaughtCardData | None = None

        self.game = None

        self._attrs_cache = {}

    def _get_cached_attr(self, name: str) -> int:
        revision = self.game.rules.revision
        cached = self._attrs_cache.get(name)
        if cached is not None and cached[0] == revision:
            return cached[1]

        get_value_func = getattr(self.game.rules, name)
        value = get_value_func(self)

        self._attrs_cache[name] = (revision, value)
        return value

    def _invalidate_rules(self) -> None:
        self.game.rules.invalidate()

    def _set_zone(self, new_zone: CardZone) -> None:
        if new_zone == self._zone:
            return

        self._zone = new_zone

    @property
    def base_identity(self) -> tuple[str, int]:
        return 'card', self.template.id

    @property
    def type(self) -> CardType:
        raise NotImplementedError

    @property
    def template_id(self) -> int:
        return self.template.id

    @property
    def template_name(self) -> str:
        return self.template.name

    @property
    def rarity(self) -> CardRarity:
        return self.template.rarity

    @property
    def cost(self) -> int:
        return self._get_cached_attr('cost')

    @property
    def base(self) -> BaseStats | TTemplate:
        return self._base or self.template

    @property
    def is_generated(self) -> bool:
        return self.creator_id is not None

    @property
    def zone(self) -> CardZone:
        return self._zone

    @zone.setter
    def zone(self, new_zone: CardZone):
        self._set_zone(new_zone)

    @property
    def controller(self) -> Entity:  # TODO add to other types of entities
        return self.game.entity(self.controller_id)

    def add_keyword(self, keyword: CardKeyword) -> None:
        self.keywords |= keyword
        self._invalidate_rules()

    def has_keyword(self, keyword: CardKeyword) -> bool:
        return keyword in self.keywords

    def remove_keyword(self, keyword: CardKeyword) -> None:
        self.keywords &= ~keyword
        self._invalidate_rules()

    def set_status(self, status_id: CardStatusId, value: int) -> None:
        if value == 0:
            self.remove_status(status_id)
        else:
            self.statuses[status_id] = value
            self._invalidate_rules()

    def get_status(self, status_id: CardStatusId) -> int:
        return self.statuses.get(status_id, 0)

    def remove_status(self, status_id: CardStatusId) -> None:
        self.statuses.pop(status_id, None)
        self._invalidate_rules()

    def set_base_stats(self, cost: int | None = None) -> None:
        source = self._base or self.template
        self._base = BaseStats(cost=source.cost if cost is None else cost)

        self._invalidate_rules()

    def _reset(self) -> None:
        pass

    def copy_exact_state_from(self, other: 'Card') -> None:
        if not isinstance(other, Card):
            raise TypeError(f"Expected Card, got {type(other).__name__}")

        if self.template.id != other.template.id:
            raise ValueError(f"Template ID mismatch: {self.template.id} != {other.template.id}")

        self._base = replace(other._base) if other._base is not None else None
        self.keywords = other.keywords
        self.statuses = other.statuses.copy()
        self.buffs = replace(other.buffs)
        self.caught_card = replace(other.caught_card) if other.caught_card is not None else None

    def get_exact_copy_attrs(self) -> dict:
        return dict(
            type=self.type,
            template=self.template,
            controller_id=self.controller_id,
            keywords=self.keywords,
            statuses=self.statuses.copy(),
            buffs=replace(self.buffs),
            caught_card=replace(self.caught_card) if self.caught_card is not None else None,
        )

    def get_snapshot_attrs(self) -> dict:
        return dict(
            **self.get_exact_copy_attrs(),
            id=self.id,
            zone=self.zone,
            creator_id=self.creator_id,
            creator_base_identity=self.creator_base_identity,
            cost=self.cost,
        )

    def to_snapshot(self) -> 'CardSnapshot':
        raise NotImplementedError

    def serialize(self) -> dict:
        return {
            'id': self.id,
            'type': self.type.value,
            'template_id': self.template.id,
            'owner_id': self.owner_id,
            'controller_id': self.controller_id,
            'zone': self._zone,
            'creator_id': self.creator_id,
            'base': asdict(self._base) if self._base is not None else None,
            'cost': self.cost,
            'keywords': self.keywords,
            'statuses': {status_id.value: value for status_id, value in self.statuses.items()},
        }


class Monster(Card[MonsterTemplate]):
    def __init__(
        self,
        id: int,
        template: MonsterTemplate,
        controller_id: PlayerId,
        zone: CardZone = CardZone.INVALID,
        creator_id: int | None = None,
        creator_base_identity: tuple[str, int] | None = None,
        base: BaseStats | None = None,
    ):
        super().__init__(id, template, controller_id, zone, creator_id, creator_base_identity, base)

        self.age = 0
        self.pos = None
        self.has_attacked = False
        self.hp_missing = 0

        self.marked_for_destruction = False

    def __str__(self):
        atk_style = 'atk-paralyzed' if self.get_status(CardStatusId.PARALYZED) else 'atk'
        hp_style = 'hp-low' if self.hp < self.max_hp else 'hp'
        return f"[{self.id}] [g]{self.cost}[/g]/[{atk_style}]{self.attack}[/{atk_style}]/[{hp_style}]{self.hp}[/{hp_style}] [monster]{self.template.name}[/monster]"

    def __repr__(self):
        return f"Monster({self.id}, {self.template!r}, {self.controller_id}, {self.zone}, {self.creator_id}, {self.base!r})"

    def _set_zone(self, new_zone: CardZone) -> None:
        if new_zone == self._zone:
            return

        # When moving a monster from board to anywhere else, reset it's state.
        if self._zone == CardZone.BOARD:
            self._reset()

        self._zone = new_zone

    def _reset(self) -> None:
        self.silence()
        self.age = 0
        self.pos = None
        self.keywords = self.template.keywords
        self.statuses = self.template.statuses.copy()

        self.has_attacked = False
        self.hp_missing = 0
        self.marked_for_destruction = False

    def to_str(self) -> str:
        atk_style = 'atk-paralyzed' if self.get_status(CardStatusId.PARALYZED) else 'atk'
        hp_style = 'hp-low' if self.hp < self.max_hp else 'hp'

        extra_symbols = ''
        if self.keywords & CardKeyword.CHARGE:
            extra_symbols += '[green]↟[/green]'
        if self.keywords & CardKeyword.HASTE:
            extra_symbols += '[yellow]↑[/yellow]'
        if self.keywords & CardKeyword.TAUNT:
            extra_symbols += '⛨'

        return f"[{self.id}] [b]{self.template.name}[/b] {extra_symbols}\n" \
               f"[{atk_style}]{self.attack}[/{atk_style}]/[{hp_style}]{self.hp}[/{hp_style}]"

    @property
    def type(self) -> CardType:
        return CardType.MONSTER

    @property
    def tribes(self) -> tuple[Tribe, ...]:
        return self.template.tribes

    @property
    def attack(self) -> int:
        return self._get_cached_attr('attack')

    @property
    def max_hp(self) -> int:
        return self._get_cached_attr('max_hp')

    @property
    def hp(self) -> int:
        return self.max_hp - self.hp_missing

    @property
    def silenced(self) -> bool:
        return self.has_keyword(CardKeyword.SILENCED)

    @property
    def can_attack(self) -> int:  # TODO deprecated?
        if self.has_attacked:
            return 0

        if self.keywords & CardKeyword.DISARMED:
            return 0

        if self.get_status(CardStatusId.PARALYZED) > 0:
            return 0

        if (self.keywords & CardKeyword.CHARGE) or self.age > 0:
            return 2

        if self.keywords & CardKeyword.HASTE:
            return 1

        return 0

    def get_ability(self, ability: Ability):
        if self.silenced:
            return None

        return super().get_ability(ability)

    def has_ability(self, ability: Ability):
        if self.silenced:
            return None

        return super().has_ability(ability)

    def has_tribe(self, tribe: Tribe) -> bool:
        return (tribe in self.template.tribes) or (Tribe.ALL in self.template.tribes)

    def heal(self, amount: int) -> int:
        old_hp = self.hp
        self.hp_missing = max(self.hp_missing - amount, 0)

        self._invalidate_rules()
        return self.hp - old_hp

    def buff(self, cost: int = 0, attack: int = 0, hp: int = 0) -> None:
        self.buffs.cost += cost
        self.buffs.attack += attack
        self.buffs.max_hp += hp

        self._invalidate_rules()

    def silence(self) -> bool:
        if self.rarity == CardRarity.DETERMINATION:
            return False

        old_hp = self.hp

        self.buffs = CardBuffs()
        self.keywords = CardKeyword.SILENCED
        self.statuses = {
            status_id: value
            for status_id, value in self.statuses.items()
            if status_id in (CardStatusId.LOOP,)
        }

        # TODO check if needed
        self._invalidate_rules()

        new_hp = min(old_hp, self.max_hp)
        self.hp_missing = max(self.max_hp - new_hp, 0)
        if self.hp <= 0:
            self.hp_missing -= 1 - self.hp

        self._invalidate_rules()
        return True

    def set_base_stats(self, cost: int | None = None, attack: int | None = None, hp: int | None = None) -> None:
        source = self._base or self.template

        self._base = BaseStats(
            cost=source.cost if cost is None else cost,
            attack=source.attack if attack is None else attack,
            hp=source.hp if hp is None else hp,
        )

        self._invalidate_rules()

    def on_turn_start(self) -> None:
        self.age += 1
        self.has_attacked = False

        paralyzed_turns = self.get_status(CardStatusId.PARALYZED)
        if paralyzed_turns >= 1:
            self.set_status(CardStatusId.PARALYZED, paralyzed_turns - 1)

        self.remove_keyword(CardKeyword.TRANSPARENCY)

    def on_turn_end(self) -> None:
        self.remove_keyword(CardKeyword.CHARGE)
        self.remove_keyword(CardKeyword.HASTE)

        if self.keywords & CardKeyword.CANDY:
            self.heal(3)

    def copy_exact_state_from(self, other: 'Card') -> None:
        if not isinstance(other, Monster):
            raise TypeError(f"Expected Monster, got {type(other).__name__}")

        super().copy_exact_state_from(other)

        self.age = other.age
        self.has_attacked = other.has_attacked
        self.hp_missing = other.hp_missing

    def get_exact_copy_attrs(self) -> dict:
        return dict(
            **super().get_exact_copy_attrs(),
            age=self.age,
            has_attacked=self.has_attacked,
            hp_missing=self.hp_missing,
        )

    def get_snapshot_attrs(self) -> dict:
        return dict(
            **super().get_snapshot_attrs(),
            pos=self.pos,
            attack=self.attack,
            hp=self.hp,
            max_hp=self.max_hp,
        )

    def to_snapshot(self) -> 'MonsterSnapshot':
        return MonsterSnapshot(**self.get_snapshot_attrs())

    def serialize(self) -> dict:
        return {
            **super().serialize(),
            'attack': self.attack,
            'hp': self.hp,
            'max_hp': self.max_hp,
        }


class Spell(Card[CardTemplate]):
    def __str__(self):
        return f"[{self.id}] [g]{self.cost}G[/g] [spell]{self.template.name}[/spell]"

    def __repr__(self):
        return f"Spell({self.id}, {self.template!r}, {self.controller_id}, {self.zone}, {self.creator_id}, {self.base!r})"

    @property
    def type(self) -> CardType:
        return CardType.SPELL

    def buff(self, cost: int = 0) -> None:
        self.buffs.cost += cost
        self._invalidate_rules()

    def to_snapshot(self) -> 'SpellSnapshot':
        return SpellSnapshot(**self.get_snapshot_attrs())


CARDS = {}


def create_card(
    id: int,
    template_id: int,
    controller_id: PlayerId,
    zone: CardZone = CardZone.INVALID,
    creator_id: int | None = None,
    creator_base_identity: tuple[str, int] | None = None,
    base_attack: int | None = None,
    base_hp: int | None = None,
) -> Card:
    template = LIBRARY.get(template_id)
    if template_id in cards:
        class_ = cards[template_id]
    else:
        class_ = (Monster, Spell)[template.type.value]

    if template.type == CardType.MONSTER and ((base_attack is not None) or (base_hp is not None)):
        base = BaseStats(
            cost=template.cost,
            attack=base_attack if base_attack is not None else template.attack,
            hp=base_hp if base_hp is not None else template.hp,
        )
    else:
        base = None

    if zone not in (CardZone.INVALID, CardZone.DECK):
        raise ValueError("This argument should only be used for deck creation. Use `Game.move_card()` instead.")

    card_ = class_(
        id=id,
        template=template,
        controller_id=controller_id,
        zone=zone,
        creator_id=creator_id,
        creator_base_identity=creator_base_identity,
        base=base,
    )

    return card_
