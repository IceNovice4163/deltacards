import copy
import json
from enum import Enum

from entity import Entity

LAST_ID = 10
cards = {}


def get_next_id():
    global LAST_ID

    LAST_ID += 1
    return LAST_ID


def card(card_id):
    def wrapper(card_class):
        if card_id in cards:
            raise ValueError(f"ID {card_id} is already assigned")

        cards[card_id] = card_class
        return card_class

    return wrapper


class TargetsEnum(Enum):
    YOU = 'you'
    OPPONENT = 'opponent'
    ALLY_MONSTER = 'ally_monster'
    ENEMY_MONSTER = 'enemy_monster'
    HAND = 'hand'
    DECK = 'deck'


class CardZone(Enum):
    INVALID = 'invalid'
    BOARD = 'board'
    HAND = 'hand'
    DECK = 'deck'
    DUSTPILE = 'dustpile'
    BURNED = 'burned'


class BaseStats:
    __slots__ = 'cost', 'attack', 'hp', 'loop'

    def __init__(self, cost: int, attack: int | None = None, hp: int | None = None, loop: int = 0):
        self.cost = cost
        self.attack = attack
        self.hp = hp
        self.loop = loop


class CardBuffs:
    __slots__ = 'cost', 'attack', 'max_hp'

    def __init__(self):
        self.cost = 0
        self.attack = 0
        self.max_hp = 0


class CardMetadata:
    __slots__ = 'fixed_id', 'name', 'rarity'

    def __init__(self, fixed_id: int, name: str, rarity: str):
        self.fixed_id = fixed_id

        self.name = name
        self.rarity = rarity


class Card(Entity):
    __slots__ = 'base', 'buffs', 'meta', 'id', 'creator_id', 'owner_id', 'extra', 'loop', '_cost', '_zone'
    targets = ()

    def __init__(
        self, base: BaseStats, fixed_id: int, name: str, rarity: str,
    ):
        self.base = base
        self.buffs = CardBuffs()
        self.meta = CardMetadata(fixed_id, name, rarity)
        self.id = get_next_id()
        self.creator_id = None
        self.owner_id = None
        self.extra = {}

        self.loop = base.loop

        self._cost = self.base.cost
        self._zone = CardZone.INVALID

    def __repr__(self):  # TODO
        return str(self)

    def _set_zone(self, new_zone: CardZone):
        if new_zone == self._zone:
            return

        if self._zone == CardZone.BOARD:
            self._reset()

        self._zone = new_zone

    @property
    def cost(self):
        return max(self._cost + self.buffs.cost, 0)

    @property
    def zone(self):
        return self._zone

    @zone.setter
    def zone(self, new_zone: CardZone):
        self._set_zone(new_zone)

    def copy(self, *, exact: bool = False, zone: CardZone = CardZone.INVALID, assign_new_id: bool = False, **kwargs):
        if exact:
            new_card = copy.deepcopy(self)
            if assign_new_id:
                new_card.id = get_next_id()

            return new_card

        return create_card(self.meta.fixed_id, zone=zone)

    def reset(self):
        pass

    def magic(self, game, target, caller):
        pass

    def dust(self, game, killer, caller):
        pass


class MonsterAttributes:
    __slots__ = 'charge', 'haste', 'taunt'

    def __init__(
        self, charge: bool = False, haste: bool = False, taunt: bool = False,
    ):
        self.charge = charge
        self.haste = haste
        self.taunt = taunt


class Monster(Card):
    __slots__ = 'attributes', 'age', 'hp', 'pos', '_attack', '_max_hp', '_silenced', '_paralyzed_turns'

    def __init__(
        self, base: BaseStats, fixed_id: int, name: str, rarity: str,
        charge: bool, haste: bool, taunt: bool,
    ):
        super().__init__(base, fixed_id, name, rarity)

        self.attributes = MonsterAttributes(charge, haste, taunt)
        self.age = 0
        self.hp = self.base.hp
        self.pos = None

        self._attack = self.base.attack
        self._max_hp = self.base.hp
        self._silenced = False
        self._paralyzed_turns = 0

    def __str__(self):
        atk_style = 'atk-paralyzed' if self._paralyzed_turns > 0 else 'atk'
        hp_style = 'hp-low' if self.hp < self.max_hp else 'hp'
        return f"[{self.id}] [g]{self.cost}[/g]/[{atk_style}]{self.attack}[/{atk_style}]/[{hp_style}]{self.hp}[/{hp_style}] [monster]{self.meta.name}[/monster]"

    def _reset(self):
        self.silence()
        self.age = 0
        self.pos = None
        self._silenced = False
        # self.attributes = MonsterAttributes(...)  # TODO

    def to_str(self):
        atk_style = 'atk-paralyzed' if self._paralyzed_turns > 0 else 'atk'
        hp_style = 'hp-low' if self.hp < self.max_hp else 'hp'

        extra_symbols = ''
        if self.attributes.charge and self.age == 0:
            extra_symbols += '[green]↟[/green]'
        if self.attributes.haste and self.age == 0:
            extra_symbols += '[yellow]↑[/yellow]'
        if self.attributes.taunt:
            extra_symbols += '⛨'

        return f"[{self.id}] [b]{self.meta.name}[/b] {extra_symbols}\n" \
               f"[{atk_style}]{self.attack}[/{atk_style}]/[{hp_style}]{self.hp}[/{hp_style}]"

    @property
    def attack(self):
        return self._attack + self.buffs.attack

    @property
    def max_hp(self):
        return self._max_hp + self.buffs.max_hp

    @property
    def can_attack(self):
        if self._paralyzed_turns > 0:
            return 0

        if self.attributes.haste:
            return 1

        if self.attributes.charge or self.age > 0:
            return 2

        return 0

    def receive_damage(self, damage: int, source = None):
        self.hp -= damage

    def heal(self, amount: int):
        old_hp = self.hp
        self.hp = min(self.hp + amount, self.max_hp)

        return self.hp - old_hp

    def buff(self, cost: int = 0, attack: int = 0, hp: int = 0):
        self.buffs.cost += cost
        self.buffs.attack += attack
        self.buffs.max_hp += hp

        if hp >= 0:
            self.hp += hp
        else:
            self.hp = min(self.hp, self.max_hp)

    def silence(self):
        self._silenced = True
        self._paralyzed_turns = 0

        self.buffs = CardBuffs()
        self.attributes = MonsterAttributes()
        self.hp = self.max_hp

    def paralyze(self):
        self._paralyzed_turns = 2

    def on_turn_start(self):
        if self._paralyzed_turns > 0:
            self._paralyzed_turns -= 1

    def on_turn_end(self):
        self.age += 1
        self.attributes.charge = False
        self.attributes.haste = False


class Spell(Card):
    def __str__(self):
        return f"[{self.id}] [g]{self.cost}G[/g] [spell]{self.meta.name}[/spell]"


CARDS = {}


def create_card(
    card_id: int,
    zone: CardZone = CardZone.INVALID,
    creator_id: int | None = None,
    owner_id: int | None = None,
):
    card_data = CARDS[card_id]
    if card_data['fixedId'] in cards:
        class_ = cards[card_data['fixedId']]
    else:
        class_ = (Monster, Spell)[card_data['typeCard']]

    if card_data['typeCard'] == 0:
        card_ = class_(
            base=BaseStats(
                cost=card_data['cost'],
                attack=card_data['attack'],
                hp=card_data['hp'],
                loop=card_data['loop'],
            ),
            fixed_id=card_data['fixedId'],
            name=card_data['name'],
            rarity=card_data['rarity'],
            charge=card_data['charge'],
            haste=card_data['haste'],
            taunt=card_data['taunt'],
        )

    elif card_data['typeCard'] == 1:
        card_ = class_(
            base=BaseStats(cost=card_data['cost'], loop=card_data['loop']),
            fixed_id=card_data['fixedId'],
            name=card_data['name'],
            rarity=card_data['rarity'],
        )

    else:
        raise ValueError('Invalid card type')

    card_.zone = zone
    if creator_id:
        card_.creator_id = creator_id

    if owner_id:
        card_.owner_id = owner_id

    return card_


def load():
    with open('cards.json') as f:
        for card_data in json.load(f):
            CARDS[card_data['fixedId']] = card_data
