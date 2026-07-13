# deltacards

An [Undercards](https://undercards.net) open-source engine implementation, written in Python.

---

## Features
- Card definition DSL with selectors, predicates, transforms & other nodes
- Support for generator- and function-based effects for complex effects that can't be expressed with pure DSL
- Non-blocking player input model, suitable for asynchronous runners

---

## Installation

Requirements: Python 3.14+

### 1. Clone the repository

```bash
git clone https://github.com/rashidsh/deltacards.git
cd deltacards
```

### 2. Setup a virtual environment

```bash
python -m venv .venv
```

Then, for Linux: `source .venv/bin/activate`

Or, for Windows: `".venv/Scripts/activate.bat"`

### 3. Install requirements

```bash
pip install -r requirements.txt
```

### 4. Download card definitions

Download a [file](https://undercards.net/AllCards) and place it in this project's root folder as `AllCards.json`

### 5. Play using CLI

```bash
python -m deltacards
```

Specify custom decks:
```bash
python -m deltacards --p1-deck "<base64/JSON deck code>" --p2-deck "<base64/JSON deck code>"
```

---

## Card Definition Examples

```python
class FukuFire(Monster):
    # Magic: Deal 3 DMG to the monster in front of this.

    magic = FRONT(SELF).hit(3)
```

---

```python
class SpadeKing(Monster):
    # Magic: Switch: [Silence all enemy monsters]
    # or [kill all enemy monsters with 2 HP or less]

    magic = Switch(
        left=ENEMY_MONSTERS.silence(),
        right=(ENEMY_MONSTERS & (HP <= 2)).kill()
    )
```

---

```python
class ChangeOfWinds(Spell):
    # Look at the next 2 cards in your deck.
    # Choose one to draw.
    # Send the other to the bottom of your deck.
    # Give them -1 COST.

    magic = YOU.choose(DECK[:2]).to(
        YOU.draw(CHOICE_SELECTED)
        >> CHOICE_NOT_SELECTED.to_deck(pos='bottom')
        >> (CHOICE_SELECTED | CHOICE_NOT_SELECTED).buff(cost=-1)
    )
```
