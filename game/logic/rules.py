from __future__ import annotations

from dataclasses import dataclass

from .models import Position, Tile, Unit


@dataclass(frozen=True)
class UnitType:
    name: str
    domain: str
    max_moves: int
    max_hp: int
    attack: int
    defense: int
    production_cost: int
    vision_range: int
    cargo_capacity: int = 0


UNIT_TYPES: dict[str, UnitType] = {
    "infantry": UnitType(
        name="infantry",
        domain="land",
        max_moves=1,
        max_hp=10,
        attack=4,
        defense=5,
        production_cost=6,
        vision_range=2,
        cargo_capacity=0,
    ),
    "tank": UnitType(
        name="tank",
        domain="land",
        max_moves=2,
        max_hp=12,
        attack=7,
        defense=5,
        production_cost=10,
        vision_range=3,
        cargo_capacity=0,
    ),
    "transport": UnitType(
        name="transport",
        domain="sea",
        max_moves=4,
        max_hp=12,
        attack=1,
        defense=4,
        production_cost=10,
        vision_range=4,
        cargo_capacity=2,
    ),
    "destroyer": UnitType(
        name="destroyer",
        domain="sea",
        max_moves=3,
        max_hp=14,
        attack=6,
        defense=6,
        production_cost=12,
        vision_range=4,
        cargo_capacity=0,
    ),
}

TERRAIN_MOVE_COSTS: dict[str, dict[str, int | None]] = {
    "plains": {"land": 1, "sea": None},
    "forest": {"land": 1, "sea": None},
    "mountain": {"land": None, "sea": None},
    "water": {"land": None, "sea": 1},
    "city": {"land": 1, "sea": None},
}

TERRAIN_DEFENSE_BONUS: dict[str, int] = {
    "plains": 0,
    "forest": 1,
    "mountain": 3,
    "water": 0,
    "city": 2,
}

CITY_PRODUCTION_PER_TURN = 2
CITY_REPAIR_PER_TURN = 3
CAPITAL_REPAIR_PER_TURN = 5
DEFAULT_CITY_BUILD = "infantry"
CITY_VISION_RANGE = 2
CAPITAL_VISION_RANGE = 4
CITY_ROLE_BUILD_OPTIONS: dict[str, tuple[str, ...]] = {
    "city": ("infantry",),
    "factory": ("infantry", "tank"),
    "harbor": ("infantry", "transport", "destroyer"),
    "capital": ("infantry", "tank"),
}


def create_unit(unit_id: int, owner_id: int, unit_type: str, position: Position) -> Unit:
    definition = UNIT_TYPES[unit_type]
    return Unit(
        unit_id=unit_id,
        owner_id=owner_id,
        unit_type=definition.name,
        position=position,
        moves_remaining=definition.max_moves,
        max_moves=definition.max_moves,
        hp=definition.max_hp,
        max_hp=definition.max_hp,
        attack=definition.attack,
        defense=definition.defense,
        domain=definition.domain,
        vision_range=definition.vision_range,
        cargo_capacity=definition.cargo_capacity,
        cargo_unit_ids=[],
    )


def terrain_move_cost(unit: Unit, tile: Tile) -> int | None:
    return TERRAIN_MOVE_COSTS[tile.terrain][unit.domain]


def resolve_combat(attacker: Unit, defender: Unit, defender_tile: Tile) -> dict[str, int | bool]:
    defense_bonus = TERRAIN_DEFENSE_BONUS[defender_tile.terrain]
    attacker_damage = max(1, attacker.attack - defender.defense + 3 - defense_bonus)
    defender_remaining_hp = max(0, defender.hp - attacker_damage)

    retaliation_damage = 0
    attacker_survived = True
    if defender_remaining_hp > 0:
        retaliation_damage = max(1, defender.attack - attacker.defense + 2 + defense_bonus)
        attacker.hp = max(0, attacker.hp - retaliation_damage)
        attacker_survived = attacker.hp > 0

    defender.hp = defender_remaining_hp
    defender_survived = defender.hp > 0

    return {
        "attacker_damage": attacker_damage,
        "defender_damage": retaliation_damage,
        "attacker_survived": attacker_survived,
        "defender_survived": defender_survived,
    }
