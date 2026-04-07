from __future__ import annotations

from dataclasses import dataclass, field

from .models import MapSize, Position, Tile, Unit
from .rules import CAPITAL_VISION_RANGE, CITY_VISION_RANGE


@dataclass
class GameState:
    map_size: MapSize
    current_player: int = 1
    turn_number: int = 1
    tiles: dict[tuple[int, int], Tile] = field(default_factory=dict)
    units: dict[int, Unit] = field(default_factory=dict)
    selected_unit_id: int | None = None
    next_unit_id: int = 1
    last_event: str = "Game created."
    explored_tiles_by_player: dict[int, set[tuple[int, int]]] = field(default_factory=dict)
    game_over: bool = False
    winner_id: int | None = None
    preview_target: Position | None = None
    pending_move_target: Position | None = None

    def is_in_bounds(self, position: Position) -> bool:
        return 0 <= position.x < self.map_size.width and 0 <= position.y < self.map_size.height

    def get_tile(self, position: Position) -> Tile:
        tile = self.tiles.get((position.x, position.y))
        if tile is None:
            raise KeyError(f"No tile exists at {position.to_dict()}.")
        return tile

    def get_unit_at(self, position: Position) -> Unit | None:
        for unit in self.units.values():
            if unit.embarked_in is not None:
                continue
            if unit.position == position:
                return unit
        return None

    def compute_visible_positions(self, player_id: int) -> set[tuple[int, int]]:
        visible: set[tuple[int, int]] = set()

        for unit in self.units.values():
            if unit.owner_id != player_id:
                continue
            if unit.embarked_in is not None:
                continue
            visible.update(self._positions_in_range(unit.position, unit.vision_range))

        for tile in self.tiles.values():
            if tile.terrain == "city" and tile.city_owner_id == player_id:
                visible.update(self._positions_in_range(tile.position, self.city_vision_range(tile.position)))

        return visible

    def remember_visible_positions(self, player_id: int, positions: set[tuple[int, int]]) -> None:
        explored = self.explored_tiles_by_player.setdefault(player_id, set())
        explored.update(positions)

    def _positions_in_range(self, center: Position, radius: int) -> set[tuple[int, int]]:
        positions: set[tuple[int, int]] = set()
        for y in range(center.y - radius, center.y + radius + 1):
            for x in range(center.x - radius, center.x + radius + 1):
                position = Position(x, y)
                if not self.is_in_bounds(position):
                    continue
                if abs(center.x - x) + abs(center.y - y) <= radius:
                    positions.add((x, y))
        return positions

    def to_visible_state(self) -> dict[str, object]:
        visible_positions = self.compute_visible_positions(self.current_player)
        explored_positions = self.explored_tiles_by_player.setdefault(self.current_player, set())
        units = [
            unit.to_dict()
            for unit in sorted(self.units.values(), key=lambda item: item.unit_id)
            if (
                (unit.owner_id == self.current_player and unit.embarked_in is not None)
                or ((unit.position.x, unit.position.y) in visible_positions and unit.embarked_in is None)
            )
        ]
        tiles = [
            {
                **tile.to_dict(),
                "visible": (tile.position.x, tile.position.y) in visible_positions,
                "explored": (tile.position.x, tile.position.y) in explored_positions,
                "city_role": self.city_role(tile.position) if tile.terrain == "city" else None,
            }
            for tile in sorted(self.tiles.values(), key=lambda item: (item.position.y, item.position.x))
        ]
        return {
            "map": self.map_size.to_dict(),
            "turn": {
                "number": self.turn_number,
                "current_player": self.current_player,
            },
            "selected_unit_id": self.selected_unit_id,
            "last_event": self.last_event,
            "game_over": self.game_over,
            "winner_id": self.winner_id,
            "preview_target": self.preview_target.to_dict() if self.preview_target is not None else None,
            "pending_move_target": self.pending_move_target.to_dict() if self.pending_move_target is not None else None,
            "tiles": tiles,
            "units": units,
        }

    def orthogonal_neighbors(self, position: Position) -> list[Position]:
        candidates = [
            Position(position.x + 1, position.y),
            Position(position.x - 1, position.y),
            Position(position.x, position.y + 1),
            Position(position.x, position.y - 1),
        ]
        return [candidate for candidate in candidates if self.is_in_bounds(candidate)]

    def is_coastal_city(self, position: Position) -> bool:
        tile = self.get_tile(position)
        if tile.terrain != "city":
            return False
        for neighbor in self.orthogonal_neighbors(position):
            if self.get_tile(neighbor).terrain == "water":
                return True
        return False

    def city_role(self, position: Position) -> str:
        tile = self.get_tile(position)
        if tile.city_role is not None:
            return tile.city_role
        if self.is_coastal_city(position):
            return "harbor"
        if tile.city_owner_id is not None:
            return "factory"
        return "city"

    def city_vision_range(self, position: Position) -> int:
        if self.city_role(position) == "capital":
            return CAPITAL_VISION_RANGE
        return CITY_VISION_RANGE

    def to_persisted_state(self) -> dict[str, object]:
        return {
            "map_size": self.map_size.to_dict(),
            "current_player": self.current_player,
            "turn_number": self.turn_number,
            "tiles": [tile.to_dict() for tile in sorted(self.tiles.values(), key=lambda item: (item.position.y, item.position.x))],
            "units": [unit.to_dict() for unit in sorted(self.units.values(), key=lambda item: item.unit_id)],
            "selected_unit_id": self.selected_unit_id,
            "next_unit_id": self.next_unit_id,
            "last_event": self.last_event,
            "game_over": self.game_over,
            "winner_id": self.winner_id,
            "preview_target": self.preview_target.to_dict() if self.preview_target is not None else None,
            "explored_tiles_by_player": {
                str(player_id): [{"x": x, "y": y} for x, y in sorted(positions)]
                for player_id, positions in sorted(self.explored_tiles_by_player.items())
            },
        }

    @classmethod
    def from_persisted_state(cls, data: dict[str, object]) -> "GameState":
        state = cls(
            map_size=MapSize.from_dict(data["map_size"]),
            current_player=int(data["current_player"]),
            turn_number=int(data["turn_number"]),
            selected_unit_id=int(data["selected_unit_id"]) if data["selected_unit_id"] is not None else None,
            next_unit_id=int(data["next_unit_id"]),
            last_event=str(data["last_event"]),
            game_over=bool(data.get("game_over", False)),
            winner_id=int(data["winner_id"]) if data.get("winner_id") is not None else None,
            preview_target=Position.from_dict(data["preview_target"]) if data.get("preview_target") is not None else None,
        )
        state.tiles = {}
        for tile_data in data["tiles"]:
            tile = Tile.from_dict(tile_data)
            state.tiles[(tile.position.x, tile.position.y)] = tile

        state.units = {}
        for unit_data in data["units"]:
            unit = Unit.from_dict(unit_data)
            state.units[unit.unit_id] = unit

        state.explored_tiles_by_player = {
            int(player_id): {(int(item["x"]), int(item["y"])) for item in positions}
            for player_id, positions in data.get("explored_tiles_by_player", {}).items()
        }
        return state
