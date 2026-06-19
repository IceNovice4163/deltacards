from deltacards.model.cards import Card, Monster


class CardContainer:
    __slots__ = '_cards',

    def __init__(self):
        self._cards: list[Card] = []

    def __str__(self):
        return ", ".join(str(card) for card in self.cards)

    def __len__(self):
        return len(self.cards)

    @property
    def cards(self) -> list[Card]:
        return self._cards

    def copy(self) -> list[Card]:
        return self._cards.copy()

    def add(self, card: Card, pos: int | None = None) -> None:
        if pos is None:
            pos = len(self.cards)

        self.cards.insert(pos, card)

    def get(self, card_id: int) -> Card:
        try:
            return next(card for card in self.cards if card.id == card_id)
        except StopIteration:
            raise StopIteration(f"Card with id {card_id} not found. Card ids: {[card.id for card in self.cards]}")

    def get_card_index(self, card: Card) -> int:
        return self.cards.index(card)

    def pop(self, index: int = 0) -> Card:
        return self.cards.pop(index)

    def remove(self, card_id: int) -> Card:
        card = self.get(card_id)
        self.cards.remove(card)

        return card

    def clear(self) -> None:
        self.cards.clear()

    def put(self, card_id: int, pos: int) -> None:
        index, card = next((index, c) for index, c in enumerate(self.cards) if c.id == card_id)

        del self.cards[index]
        self.cards.insert(pos, card)


class Deck(CardContainer):
    def __init__(self, cards: list[Card]):
        if len(cards) != 25:
            raise ValueError(f"Invalid deck size: {len(cards)}")

        super().__init__()

        self._cards = cards.copy()


class Board(CardContainer):
    __slots__ = ()
    MAX_CARDS = 4

    def __init__(self):
        self._cards: list[Monster | None] = [None] * 4

    def __getitem__(self, key):
        return self._cards[key]

    def __setitem__(self, key, value):
        self._cards[key] = value

    def __len__(self):
        return sum(1 for monster in self._cards if monster)

    @property
    def cards(self) -> list[Monster]:
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
        return next(card for card in self._cards if card and card.id == card_id)

    def get_empty_slot_index(self) -> int:
        return next(index for index, card in enumerate(self._cards) if card is None)

    def remove(self, card_id: int) -> Monster:
        card = self.get(card_id)
        index = self._cards.index(card)
        self._cards[index] = None

        return card
