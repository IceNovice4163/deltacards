import random

from cards import CardZone, Card, Monster, create_card


class CardContainer:
    __slots__ = '_cards',

    def __init__(self, card_ids: list[int]):
        self._cards: list[Card] = [create_card(fixed_id) for fixed_id in card_ids]

    def __str__(self):
        return ", ".join(str(card) for card in self.cards)

    def __len__(self):
        return len(self.cards)

    @property
    def cards(self):
        return self._cards

    def add(self, card: Card) -> None:
        self.cards.append(card)

    def get(self, card_id: int) -> Card:
        try:
            return next(card for card in self.cards if card.id == card_id)
        except StopIteration:
            raise StopIteration(f"Card with id {card_id} not found. Card ids: {[card.id for card in self.cards]}")

    def get_card_index(self, card: Card) -> int:
        return self.cards.index(card)

    def pop(self, card_id: int) -> Card:
        card = self.get(card_id)
        self.cards.remove(card)

        return card

    def clear(self) -> None:
        self.cards.clear()


class Deck(CardContainer):
    __slots__ = ()

    def __init__(self, card_ids: list[int], shuffle: bool = False):
        if len(card_ids) != 25:
            raise ValueError(f"Invalid deck size: {len(card_ids)}")

        if shuffle:
            random.shuffle(card_ids)

        self._cards: list[Card] = [create_card(fixed_id, zone=CardZone.DECK) for fixed_id in card_ids]


class Board(CardContainer):
    __slots__ = ()
    MAX_CARDS = 4

    def __init__(self, card_ids: list[int | None] = None):
        if card_ids is None:
            card_ids = [None, None, None, None]

        if len(card_ids) != self.MAX_CARDS:
            raise ValueError(f"Invalid board size: {len(card_ids)}")

        self._cards: list[Monster] = [
            create_card(fixed_id, zone=CardZone.BOARD)
            if fixed_id else None for fixed_id in card_ids
        ]

    def __getitem__(self, key):
        return self._cards[key]

    def __setitem__(self, key, value):
        self._cards[key] = value

    def __len__(self):
        return sum(1 for monster in self._cards if monster)

    @property
    def cards(self):
        return [monster for monster in self._cards if monster]

    def add(self, card: Monster, pos: int | None = None) -> int:
        if pos is None:
            pos = 0
            while pos <= 3:
                if not self._cards[pos]:
                    break

                pos += 1
                if pos == 4:
                    raise ValueError("Board is full")

        self._cards[pos] = card
        return pos

    def get(self, card_id: int) -> Monster:
        return next(card for card in self.cards if card and card.id == card_id)

    def pop(self, card_id: int) -> Monster:
        card = self.get(card_id)
        index = self._cards.index(card)
        self._cards[index] = None

        return card
