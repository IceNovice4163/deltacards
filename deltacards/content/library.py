from deltacards.model.enums import (
    CardKeyword,
    CardRarity,
    CardStatusId,
    CardToggleableAbility,
    CardType,
    Expansion,
    Tribe,
)
from deltacards.model.templates import CardTemplate, MonsterTemplate, SpellTemplate


class CardLibrary:
    def __init__(self):
        self._by_id: dict[int, 'CardTemplate'] = {}
        self._by_name: dict[str, 'CardTemplate'] = {}

    def get(self, fixed_id: int) -> 'CardTemplate':
        return self._by_id[fixed_id]

    def get_by_name(self, name: str) -> 'CardTemplate':
        return self._by_name[name.lower()]

    def _load_template(self, d: dict) -> 'CardTemplate':
        card_id = d['fixedId']

        keywords = CardKeyword.NONE
        statuses = {}
        active_abilities = set()

        for status in d['statuses']:
            match status['name']:
                case 'charge':
                    keywords |= CardKeyword.CHARGE
                case 'haste':
                    keywords |= CardKeyword.HASTE
                case 'taunt':
                    keywords |= CardKeyword.TAUNT
                case 'kr':
                    keywords |= CardKeyword.KR
                case 'candy':
                    keywords |= CardKeyword.CANDY
                case 'armor':
                    keywords |= CardKeyword.ARMOR
                case 'transparency':
                    keywords |= CardKeyword.TRANSPARENCY
                case 'disarmed':
                    keywords |= CardKeyword.DISARMED
                case 'invulnerable':
                    keywords |= CardKeyword.INVULNERABLE
                case 'wanted':
                    keywords |= CardKeyword.WANTED
                case 'darkspawn':
                    keywords |= CardKeyword.DARKSPAWN
                case 'paralyzed':
                    statuses[CardStatusId.PARALYZED] = status['counter']
                case 'dodge':
                    statuses[CardStatusId.DODGE] = status['counter']
                case 'loop':
                    statuses[CardStatusId.LOOP] = status['counter']
                case 'shock':
                    active_abilities.add(CardToggleableAbility.SHOCK)
                case 'support':
                    active_abilities.add(CardToggleableAbility.SUPPORT)
                case 'bullseye':
                    active_abilities.add(CardToggleableAbility.BULLSEYE)
                case 'program':
                    active_abilities.add(CardToggleableAbility.PROGRAM)
                case _:
                    raise RuntimeError(f"Unknown card status {status['name']} on card with ID {card_id}")

        # TODO
        # Read and set abilities of cards based on their actual implementation classes
        from deltacards.model.cards import cards
        card_cls = cards.get(card_id)
        if card_cls is not None:
            abilities = cards[card_id].declared_ability_names()
        else:
            abilities = set()

        common = dict(
            id=card_id,
            name=d['name'],
            rarity=CardRarity[d['rarity']],
            cost=d['cost'],
            abilities=abilities,
            keywords=keywords,
            statuses=statuses,
            active_abilities=active_abilities,
            expansion=Expansion(d['extension'].lower()),
            tribes=tuple(Tribe(tribe_id.lower()) for tribe_id in d['tribes']),
            soul_id=d['soul']['name'].lower() if d.get('soul') else None,
        )

        # TODO temporary name fix as it's non-localized name in the cards file is incorrect
        if common['id'] == 270:
            common['name'] = "Thrashing Machine"

        match d['typeCard']:
            case CardType.MONSTER.value:
                return MonsterTemplate(
                    **common,
                    attack=int(d['attack']),
                    hp=int(d['hp']),
                )
            case CardType.SPELL.value:
                return SpellTemplate(**common)
            case _:
                raise ValueError("Invalid card type")

    def load_templates(self, data: list) -> None:
        for d in data:
            template = self._load_template(d)
            self._by_id[template.id] = template
            self._by_name[template.name.lower()] = template


LIBRARY = CardLibrary()
