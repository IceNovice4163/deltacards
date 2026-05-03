from cards.templates import CardTemplate, MonsterTemplate, SpellTemplate
from enums import CardKeyword, CardRarity, CardStatusId, CardType


class CardLibrary:
    def __init__(self):
        self._by_id: dict[int, 'CardTemplate'] = {}
        self._by_name: dict[str, 'CardTemplate'] = {}

    def get(self, fixed_id: int) -> 'CardTemplate':
        return self._by_id[fixed_id]

    def get_by_name(self, name: str) -> 'CardTemplate':
        return self._by_name[name.lower()]

    def _load_template(self, d: dict) -> 'CardTemplate':
        keywords = CardKeyword.NONE
        statuses = {}

        for status in d['statuses']:
            match status['name']:
                case 'charge':
                    keywords |= CardKeyword.CHARGE
                case 'haste':
                    keywords |= CardKeyword.HASTE
                case 'taunt':
                    keywords |= CardKeyword.TAUNT
                case 'loop':
                    statuses[CardStatusId.LOOP] = status['counter']

        common = dict(
            id=d['fixedId'],
            name=d['name'],
            rarity=CardRarity[d['rarity']],
            cost=d['cost'],
            keywords=keywords,
            statuses=statuses,
        )

        match d['typeCard']:
            case CardType.MONSTER.value:
                return MonsterTemplate(**common, attack=int(d['attack']), hp=int(d['hp']))
            case CardType.SPELL.value:
                return SpellTemplate(**common)
            case _:
                raise ValueError("Invalid card type")

    def load_templates(self, data: list) -> None:
        for d in data:
            template = self._load_template(d)
            self._by_id[template.id] = template
            self._by_name[template.name.lower().replace(" ", "")] = template  # TODO replace all special symbols?


LIBRARY = CardLibrary()
