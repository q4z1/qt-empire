from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    x: int
    y: int

    def to_dict(self) -> dict[str, int]:
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "Position":
        return cls(x=int(data["x"]), y=int(data["y"]))


@dataclass
class Unit:
    unit_id: int
    owner_id: int
    unit_type: str
    position: Position
    moves_remaining: int
    max_moves: int
    hp: int
    max_hp: int
    attack: int
    defense: int
    attack_range: int
    domain: str
    vision_range: int
    cargo_capacity: int
    cargo_unit_ids: list[int]
    embarked_in: int | None = None
    queued_destination: Position | None = None

    def to_dict(self) -> dict[str, int | str | None | dict[str, int]]:
        return {
            "id": self.unit_id,
            "owner_id": self.owner_id,
            "unit_type": self.unit_type,
            "position": self.position.to_dict(),
            "moves_remaining": self.moves_remaining,
            "max_moves": self.max_moves,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "defense": self.defense,
            "attack_range": self.attack_range,
            "domain": self.domain,
            "vision_range": self.vision_range,
            "cargo_capacity": self.cargo_capacity,
            "cargo_unit_ids": list(self.cargo_unit_ids),
            "cargo_count": len(self.cargo_unit_ids),
            "embarked_in": self.embarked_in,
            "queued_destination": self.queued_destination.to_dict() if self.queued_destination is not None else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Unit":
        return cls(
            unit_id=int(data["id"]),
            owner_id=int(data["owner_id"]),
            unit_type=str(data["unit_type"]),
            position=Position.from_dict(data["position"]),
            moves_remaining=int(data["moves_remaining"]),
            max_moves=int(data["max_moves"]),
            hp=int(data["hp"]),
            max_hp=int(data["max_hp"]),
            attack=int(data["attack"]),
            defense=int(data["defense"]),
            attack_range=int(data.get("attack_range", 1)),
            domain=str(data["domain"]),
            vision_range=int(data["vision_range"]),
            cargo_capacity=int(data["cargo_capacity"]),
            cargo_unit_ids=[int(item) for item in data["cargo_unit_ids"]],
            embarked_in=int(data["embarked_in"]) if data["embarked_in"] is not None else None,
            queued_destination=Position.from_dict(data["queued_destination"]) if data.get("queued_destination") is not None else None,
        )


@dataclass(frozen=True)
class MapSize:
    width: int
    height: int

    def to_dict(self) -> dict[str, int]:
        return {"width": self.width, "height": self.height}

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "MapSize":
        return cls(width=int(data["width"]), height=int(data["height"]))


@dataclass(frozen=True)
class Tile:
    position: Position
    terrain: str
    city_owner_id: int | None = None
    production_points: int = 0
    build_choice: str | None = None
    city_role: str | None = None

    def to_dict(self) -> dict[str, int | str | None | dict[str, int]]:
        return {
            "position": self.position.to_dict(),
            "terrain": self.terrain,
            "city_owner_id": self.city_owner_id,
            "production_points": self.production_points,
            "build_choice": self.build_choice,
            "city_role": self.city_role,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Tile":
        return cls(
            position=Position.from_dict(data["position"]),
            terrain=str(data["terrain"]),
            city_owner_id=int(data["city_owner_id"]) if data["city_owner_id"] is not None else None,
            production_points=int(data["production_points"]),
            build_choice=str(data["build_choice"]) if data.get("build_choice") is not None else None,
            city_role=str(data["city_role"]) if data.get("city_role") is not None else None,
        )
