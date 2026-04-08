"""Simple AI player for Empire.

The AI operates entirely through the public GameAPI and reads only the
internal GameState for efficient data access (no network, no UI).

Strategy (easy difficulty):
- For every unit that still has moves: find the nearest high-value target
  (enemy capital → enemy city → enemy unit) and move one step toward it.
  If an enemy is directly adjacent, attack immediately.
- Artillery bombards the nearest visible enemy in range.
- Transports carrying cargo head toward the nearest land coast adjacent to
  an enemy or neutral city. Empty transports stay put.
- Each owned city without a build order gets one set automatically based on
  its role: capital/factory → tank, harbor → destroyer, city → infantry.
"""

from __future__ import annotations

import heapq
from typing import TYPE_CHECKING

from .models import Position
from .rules import CITY_ROLE_BUILD_OPTIONS, UNIT_TYPES, terrain_move_cost

if TYPE_CHECKING:
    from .api import GameAPI
    from .state import GameState


class AIPlayer:
    """Drives a single AI-controlled player through the GameAPI."""

    def __init__(self, player_id: int) -> None:
        self.player_id = player_id

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def take_turn(self, api: "GameAPI") -> None:
        """Execute one full AI turn: move all units, then call end_turn."""
        state = api._state
        if state.current_player != self.player_id:
            return

        self._set_production(state, api)
        self._move_all_units(state, api)
        api.end_turn()

    # ------------------------------------------------------------------
    # Production
    # ------------------------------------------------------------------

    def _set_production(self, state: "GameState", api: "GameAPI") -> None:
        for tile in state.tiles.values():
            if tile.terrain != "city":
                continue
            if tile.city_owner_id != self.player_id:
                continue
            if tile.build_choice is not None:
                continue
            role = state.city_role(tile.position) or "city"
            options = CITY_ROLE_BUILD_OPTIONS.get(role, ("infantry",))
            # Prefer stronger unit types: tank > infantry, destroyer > transport
            preference = ("tank", "artillery", "destroyer", "infantry", "transport")
            choice = next((u for u in preference if u in options), options[0])
            api.set_city_production(tile.position, choice)

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------

    def _move_all_units(self, state: "GameState", api: "GameAPI") -> None:
        # Collect unit IDs upfront — the dict may change as units are
        # created/destroyed during the loop.
        unit_ids = [
            uid for uid, u in state.units.items()
            if u.owner_id == self.player_id and u.embarked_in is None
        ]
        for uid in unit_ids:
            unit = state.units.get(uid)
            if unit is None or unit.owner_id != self.player_id:
                continue
            if unit.embarked_in is not None:
                continue
            self._act_unit(unit, state, api)

    def _act_unit(self, unit, state: "GameState", api: "GameAPI") -> None:
        """Act with a single unit until it runs out of moves."""
        max_iter = unit.max_moves + 2  # safety cap
        for _ in range(max_iter):
            unit = state.units.get(unit.unit_id)
            if unit is None or unit.moves_remaining <= 0:
                break
            moved = self._act_once(unit, state, api)
            if not moved:
                break

    def _act_once(self, unit, state: "GameState", api: "GameAPI") -> bool:
        """One action for a unit. Returns True if the unit did something."""
        # Artillery: bombard if a target is in range
        if unit.attack_range >= 2:
            if self._try_bombard(unit, state, api):
                return False  # artillery used its turn
            return False  # artillery can't move-and-attack; end its turn

        # Land/sea units: attack adjacent enemy first
        for neighbor in _orthogonal_neighbors(unit.position, state):
            occ = state.get_unit_at(neighbor)
            if occ is not None and occ.owner_id != self.player_id:
                api.move_unit(unit.unit_id, neighbor)
                return False  # attack consumed the move

        # Capture neutral/enemy city if standing on adjacent tile
        for neighbor in _orthogonal_neighbors(unit.position, state):
            tile = state.get_tile(neighbor)
            if tile.terrain == "city" and tile.city_owner_id != self.player_id:
                occ = state.get_unit_at(neighbor)
                if occ is None:
                    api.move_unit(unit.unit_id, neighbor)
                    return True

        # Move toward nearest high-value target
        target = self._nearest_target(unit, state)
        if target is None:
            return False

        step = self._next_step_toward(unit, target, state)
        if step is None:
            return False

        result = api.move_unit(unit.unit_id, step)
        return result.ok

    def _try_bombard(self, unit, state: "GameState", api: "GameAPI") -> bool:
        """Artillery: attack the nearest in-range enemy. Returns True if fired."""
        attack_range = unit.attack_range
        best: tuple[int, object] | None = None
        for distance in range(2, attack_range + 1):
            for dx, dy in ((-distance, 0), (distance, 0), (0, -distance), (0, distance)):
                target = Position(unit.position.x + dx, unit.position.y + dy)
                if not state.is_in_bounds(target):
                    continue
                occ = state.get_unit_at(target)
                if occ is None or occ.owner_id == self.player_id:
                    continue
                if not _line_clear(unit.position, target, state):
                    continue
                if best is None or distance < best[0]:
                    best = (distance, target)
        if best is None:
            return False
        api.move_unit(unit.unit_id, best[1])
        return True

    # ------------------------------------------------------------------
    # Target selection
    # ------------------------------------------------------------------

    def _nearest_target(self, unit, state: "GameState") -> Position | None:
        """Return the coordinates of the best target for this unit."""
        candidates: list[tuple[int, Position]] = []

        for tile in state.tiles.values():
            if tile.terrain != "city":
                continue
            if tile.city_owner_id == self.player_id:
                continue
            # Prioritize enemy capitals, then other cities
            role = state.city_role(tile.position) or "city"
            priority = 0 if role == "capital" else 1
            dist = _manhattan(unit.position, tile.position)
            candidates.append((priority * 1000 + dist, tile.position))

        for enemy_unit in state.units.values():
            if enemy_unit.owner_id == self.player_id:
                continue
            if enemy_unit.embarked_in is not None:
                continue
            domain_match = enemy_unit.domain == unit.domain
            dist = _manhattan(unit.position, enemy_unit.position)
            priority = 2 if domain_match else 3
            candidates.append((priority * 1000 + dist, enemy_unit.position))

        if not candidates:
            return None
        candidates.sort(key=lambda c: c[0])
        return candidates[0][1]

    # ------------------------------------------------------------------
    # Pathfinding (minimal, mirrors GameAPI._find_path logic)
    # ------------------------------------------------------------------

    def _next_step_toward(self, unit, target: Position, state: "GameState") -> Position | None:
        """Return the next adjacent step on the shortest path to target."""
        start = unit.position
        frontier: list[tuple[int, int, Position]] = [(0, 0, start)]
        best_costs: dict[tuple[int, int], int] = {(start.x, start.y): 0}
        previous: dict[tuple[int, int], tuple[int, int] | None] = {(start.x, start.y): None}
        seq = 1

        while frontier:
            cost, _, current = heapq.heappop(frontier)
            key = (current.x, current.y)
            if cost != best_costs[key]:
                continue
            if current == target:
                return self._first_step(previous, start, target)
            for neighbor in _orthogonal_neighbors(current, state):
                if not _can_step_onto(unit, neighbor, target, state, self.player_id):
                    continue
                tile = state.get_tile(neighbor)
                move_cost = terrain_move_cost(unit, tile)
                if move_cost is None:
                    continue
                nkey = (neighbor.x, neighbor.y)
                next_cost = cost + move_cost
                if next_cost >= best_costs.get(nkey, 1_000_000):
                    continue
                best_costs[nkey] = next_cost
                previous[nkey] = key
                heapq.heappush(frontier, (next_cost, seq, neighbor))
                seq += 1

        return None

    def _first_step(
        self,
        previous: dict[tuple[int, int], tuple[int, int] | None],
        start: Position,
        target: Position,
    ) -> Position | None:
        path: list[Position] = []
        current: tuple[int, int] | None = (target.x, target.y)
        while current is not None:
            path.append(Position(current[0], current[1]))
            current = previous.get(current)
        path.reverse()
        # path[0] == start, path[1] is the first step
        if len(path) < 2:
            return None
        return path[1]


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _orthogonal_neighbors(pos: Position, state: "GameState") -> list[Position]:
    candidates = [
        Position(pos.x + 1, pos.y),
        Position(pos.x - 1, pos.y),
        Position(pos.x, pos.y + 1),
        Position(pos.x, pos.y - 1),
    ]
    return [p for p in candidates if state.is_in_bounds(p)]


def _manhattan(a: Position, b: Position) -> int:
    return abs(a.x - b.x) + abs(a.y - b.y)


def _can_step_onto(unit, pos: Position, target: Position, state: "GameState", player_id: int) -> bool:
    occ = state.get_unit_at(pos)
    if occ is None:
        return True
    if pos == unit.position:
        return True
    if pos != target:
        return False
    return occ.owner_id != player_id


def _line_clear(start: Position, target: Position, state: "GameState") -> bool:
    """True if there is no blocking terrain between start and target (cardinal only)."""
    from .rules import RANGE_BLOCKING_TERRAINS
    if start.x == target.x:
        step_y = 1 if target.y > start.y else -1
        for y in range(start.y + step_y, target.y, step_y):
            tile = state.tiles.get((start.x, y))
            if tile and tile.terrain in RANGE_BLOCKING_TERRAINS:
                return False
    elif start.y == target.y:
        step_x = 1 if target.x > start.x else -1
        for x in range(start.x + step_x, target.x, step_x):
            tile = state.tiles.get((x, start.y))
            if tile and tile.terrain in RANGE_BLOCKING_TERRAINS:
                return False
    return True
