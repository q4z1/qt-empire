from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .models import Position
from .rules import CAPITAL_REPAIR_PER_TURN, CITY_REPAIR_PER_TURN, CITY_PRODUCTION_PER_TURN, CITY_ROLE_BUILD_OPTIONS, DEFAULT_CITY_BUILD, UNIT_TYPES, create_unit, resolve_combat, terrain_move_cost
from .scenarios import create_default_state, create_scenario_state
from .state import GameState


@dataclass
class CommandResult:
    ok: bool
    message: str
    state: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {"ok": self.ok, "message": self.message, "state": self.state}


class GameAPI:
    def __init__(self, state: GameState):
        self._state = state
        self._refresh_visibility_memory()

    def get_visible_state(self) -> dict[str, object]:
        self._refresh_visibility_memory()
        state = self._state.to_visible_state()
        state["legal_targets"] = self.get_legal_targets()
        self._attach_city_build_options(state)
        return state

    def select_unit(self, unit_id: int) -> CommandResult:
        inactive_result = self._ensure_game_active()
        if inactive_result is not None:
            return inactive_result
        unit = self._state.units.get(unit_id)
        if unit is None:
            return self._result(False, f"Unit {unit_id} does not exist.")
        if unit.owner_id != self._state.current_player:
            return self._result(False, f"Unit {unit_id} is not controlled by player {self._state.current_player}.")

        self._state.selected_unit_id = unit_id
        return self._result(True, f"Selected unit {unit_id}.")

    def move_unit(self, unit_id: int, target_position: dict[str, int] | Position) -> CommandResult:
        inactive_result = self._ensure_game_active()
        if inactive_result is not None:
            return inactive_result
        unit = self._state.units.get(unit_id)
        if unit is None:
            return self._result(False, f"Unit {unit_id} does not exist.")
        if unit.owner_id != self._state.current_player:
            return self._result(False, f"Unit {unit_id} is not controlled by player {self._state.current_player}.")

        target = self._normalize_position(target_position)
        if not self._state.is_in_bounds(target):
            return self._result(False, f"Target {target.to_dict()} is outside the map.")

        if unit.embarked_in is not None:
            return self._disembark_unit(unit, target)

        distance = abs(unit.position.x - target.x) + abs(unit.position.y - target.y)
        if distance != 1:
            return self._result(False, "Only orthogonal single-tile movement is supported.")

        target_tile = self._state.get_tile(target)
        blocking_unit = self._state.get_unit_at(target)

        if blocking_unit is not None and blocking_unit.owner_id == unit.owner_id:
            if self._can_embark(unit, blocking_unit):
                return self._embark_unit(unit, blocking_unit)
            return self._result(False, f"Tile {target.to_dict()} is occupied by friendly unit {blocking_unit.unit_id}.")

        if self._can_transport_unload(unit, target_tile, blocking_unit):
            cargo_unit = self._state.units[unit.cargo_unit_ids[0]]
            return self._disembark_unit(cargo_unit, target)

        move_cost = terrain_move_cost(unit, target_tile)
        if move_cost is None:
            return self._result(False, f"{unit.unit_type} cannot enter {target_tile.terrain}.")
        if unit.moves_remaining < move_cost:
            return self._result(False, f"Unit {unit_id} needs {move_cost} movement points.")

        if blocking_unit is not None and blocking_unit.owner_id != unit.owner_id:
            return self._resolve_attack(unit, blocking_unit, target_tile)

        unit.position = target
        unit.moves_remaining -= move_cost
        self._sync_cargo_positions(unit)
        self._capture_city_if_present(unit)
        self._state.selected_unit_id = unit_id
        if self._state.game_over:
            return self._result(True, self._state.last_event)
        self._state.last_event = f"Moved unit {unit_id} to {target.to_dict()}."
        return self._result(True, self._state.last_event)

    def end_turn(self) -> CommandResult:
        inactive_result = self._ensure_game_active()
        if inactive_result is not None:
            return inactive_result
        self._state.current_player = 2 if self._state.current_player == 1 else 1
        self._state.turn_number += 1
        self._state.selected_unit_id = None

        support_messages = self._apply_city_support()
        production_messages = self._apply_city_production()
        message = f"Turn {self._state.turn_number} started for player {self._state.current_player}."
        if support_messages:
            message = f"{message} {' '.join(support_messages)}"
        if production_messages:
            message = f"{message} {' '.join(production_messages)}"
        self._state.last_event = message

        return self._result(True, message)

    def set_city_production(self, position: dict[str, int] | Position, unit_type: str) -> CommandResult:
        inactive_result = self._ensure_game_active()
        if inactive_result is not None:
            return inactive_result
        target = self._normalize_position(position)
        tile = self._state.get_tile(target)
        if tile.terrain != "city":
            return self._result(False, f"Tile {target.to_dict()} is not a city.")
        if tile.city_owner_id != self._state.current_player:
            return self._result(False, f"City at {target.to_dict()} is not controlled by player {self._state.current_player}.")
        if unit_type not in self._city_build_options_for_tile(tile):
            return self._result(False, f"{unit_type} is not a valid build for city at {target.to_dict()}.")

        self._state.tiles[(target.x, target.y)] = tile.__class__(
            position=tile.position,
            terrain=tile.terrain,
            city_owner_id=tile.city_owner_id,
            production_points=tile.production_points,
            build_choice=unit_type,
            city_role=tile.city_role,
        )
        self._state.last_event = f"City at {target.to_dict()} now builds {unit_type}."
        return self._result(True, self._state.last_event)

    def save_to_file(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self._state.to_persisted_state(), indent=2), encoding="utf-8")
        return target

    def _normalize_position(self, position: dict[str, int] | Position) -> Position:
        if isinstance(position, Position):
            return position
        return Position(x=int(position["x"]), y=int(position["y"]))

    def get_legal_targets(self, unit_id: int | None = None) -> list[dict[str, object]]:
        selected_unit_id = unit_id if unit_id is not None else self._state.selected_unit_id
        if selected_unit_id is None:
            return []

        unit = self._state.units.get(selected_unit_id)
        if unit is None or unit.owner_id != self._state.current_player:
            return []

        if unit.embarked_in is not None:
            return self._legal_disembark_targets(unit)

        legal_targets: list[dict[str, object]] = []
        for neighbor in self._state.orthogonal_neighbors(unit.position):
            legal_target = self._classify_target(unit, neighbor)
            if legal_target is not None:
                legal_targets.append(legal_target)
        return legal_targets

    def _classify_target(self, unit, target: Position) -> dict[str, object] | None:
        tile = self._state.get_tile(target)
        occupant = self._state.get_unit_at(target)

        if occupant is not None and occupant.owner_id == unit.owner_id:
            if self._can_embark(unit, occupant) and unit.moves_remaining >= 1:
                return self._target_payload(target, "embark", f"Embark on transport #{occupant.unit_id}")
            return None

        if self._can_transport_unload(unit, tile, occupant) and unit.moves_remaining >= 1:
            cargo_id = unit.cargo_unit_ids[0]
            return self._target_payload(target, "disembark", f"Unload cargo #{cargo_id}")

        move_cost = terrain_move_cost(unit, tile)
        if move_cost is None or unit.moves_remaining < move_cost:
            return None

        if occupant is not None and occupant.owner_id != unit.owner_id:
            return self._target_payload(target, "attack", f"Attack unit #{occupant.unit_id}")

        return self._target_payload(target, "move", f"Move to {target.to_dict()}")

    def _legal_disembark_targets(self, unit) -> list[dict[str, object]]:
        carrier = self._state.units.get(unit.embarked_in)
        if carrier is None or carrier.moves_remaining < 1:
            return []

        legal_targets: list[dict[str, object]] = []
        for neighbor in self._state.orthogonal_neighbors(carrier.position):
            tile = self._state.get_tile(neighbor)
            if self._state.get_unit_at(neighbor) is not None:
                continue
            if terrain_move_cost(unit, tile) is None:
                continue
            legal_targets.append(self._target_payload(neighbor, "disembark", f"Disembark to {neighbor.to_dict()}"))
        return legal_targets

    def _target_payload(self, position: Position, action_type: str, label: str) -> dict[str, object]:
        return {
            "position": position.to_dict(),
            "action_type": action_type,
            "label": label,
        }

    def _can_embark(self, unit, carrier) -> bool:
        return (
            unit.domain == "land"
            and unit.embarked_in is None
            and carrier.unit_type == "transport"
            and len(carrier.cargo_unit_ids) < carrier.cargo_capacity
        )

    def _embark_unit(self, unit, carrier) -> CommandResult:
        if unit.moves_remaining < 1:
            return self._result(False, f"Unit {unit.unit_id} has no movement left.")

        unit.embarked_in = carrier.unit_id
        unit.position = carrier.position
        unit.moves_remaining = 0
        carrier.cargo_unit_ids.append(unit.unit_id)
        self._state.selected_unit_id = carrier.unit_id
        self._state.last_event = f"Unit {unit.unit_id} embarked on transport {carrier.unit_id}."
        return self._result(True, self._state.last_event)

    def _disembark_unit(self, unit, target) -> CommandResult:
        carrier = self._state.units.get(unit.embarked_in)
        if carrier is None:
            return self._result(False, f"Transport for unit {unit.unit_id} no longer exists.")

        distance = abs(carrier.position.x - target.x) + abs(carrier.position.y - target.y)
        if distance != 1:
            return self._result(False, "Disembark requires an orthogonally adjacent tile.")

        target_tile = self._state.get_tile(target)
        if self._state.get_unit_at(target) is not None:
            return self._result(False, f"Tile {target.to_dict()} is occupied.")
        move_cost = terrain_move_cost(unit, target_tile)
        if move_cost is None:
            return self._result(False, f"{unit.unit_type} cannot disembark onto {target_tile.terrain}.")
        if carrier.moves_remaining < 1:
            return self._result(False, f"Transport {carrier.unit_id} has no movement left for unloading.")

        unit.embarked_in = None
        unit.position = target
        unit.moves_remaining = 0
        carrier.moves_remaining -= 1
        carrier.cargo_unit_ids = [cargo_id for cargo_id in carrier.cargo_unit_ids if cargo_id != unit.unit_id]
        self._capture_city_if_present(unit)
        self._state.selected_unit_id = unit.unit_id
        self._state.last_event = f"Unit {unit.unit_id} disembarked from transport {carrier.unit_id} to {target.to_dict()}."
        return self._result(True, self._state.last_event)

    def _can_transport_unload(self, unit, target_tile, blocking_unit) -> bool:
        if unit.unit_type != "transport" or not unit.cargo_unit_ids or blocking_unit is not None:
            return False
        cargo_unit = self._state.units[unit.cargo_unit_ids[0]]
        return terrain_move_cost(cargo_unit, target_tile) is not None

    def _resolve_attack(self, attacker, defender, defender_tile) -> CommandResult:
        if attacker.moves_remaining < 1:
            return self._result(False, f"Unit {attacker.unit_id} has no movement left.")

        combat = resolve_combat(attacker, defender, defender_tile)
        attacker.moves_remaining = 0

        if not combat["attacker_survived"]:
            self._destroy_unit(attacker.unit_id)
            self._state.selected_unit_id = None

        if not combat["defender_survived"]:
            self._destroy_unit(defender.unit_id)
            if combat["attacker_survived"]:
                attacker.position = defender.position
                self._sync_cargo_positions(attacker)
                self._capture_city_if_present(attacker)

        if combat["attacker_survived"]:
            self._state.selected_unit_id = attacker.unit_id

        if self._state.game_over:
            return self._result(True, self._state.last_event)

        message = (
            f"Unit {attacker.unit_id} attacked unit {defender.unit_id}: "
            f"defender -{combat['attacker_damage']} HP, attacker -{combat['defender_damage']} HP."
        )
        if not combat["defender_survived"]:
            message += f" Defender {defender.unit_id} destroyed."
        if not combat["attacker_survived"]:
            message += f" Attacker {attacker.unit_id} destroyed."
        self._state.last_event = message
        return self._result(True, message)

    def _destroy_unit(self, unit_id: int) -> None:
        unit = self._state.units.get(unit_id)
        if unit is None:
            return

        if unit.embarked_in is not None:
            carrier = self._state.units.get(unit.embarked_in)
            if carrier is not None:
                carrier.cargo_unit_ids = [cargo_id for cargo_id in carrier.cargo_unit_ids if cargo_id != unit_id]

        for cargo_id in list(unit.cargo_unit_ids):
            self._destroy_unit(cargo_id)

        del self._state.units[unit_id]

    def _sync_cargo_positions(self, carrier) -> None:
        for cargo_id in carrier.cargo_unit_ids:
            cargo_unit = self._state.units.get(cargo_id)
            if cargo_unit is not None:
                cargo_unit.position = carrier.position

    def _capture_city_if_present(self, unit) -> None:
        tile = self._state.get_tile(unit.position)
        if tile.terrain == "city" and tile.city_owner_id != unit.owner_id:
            previous_owner_id = tile.city_owner_id
            build_choice = tile.build_choice or DEFAULT_CITY_BUILD
            if build_choice not in self._city_build_options_for_tile(tile):
                build_choice = DEFAULT_CITY_BUILD
            self._state.tiles[(tile.position.x, tile.position.y)] = tile.__class__(
                position=tile.position,
                terrain=tile.terrain,
                city_owner_id=unit.owner_id,
                production_points=tile.production_points,
                build_choice=build_choice,
                city_role=tile.city_role,
            )
            self._check_capital_victory(previous_owner_id)

    def _apply_city_production(self) -> list[str]:
        messages: list[str] = []
        for key, tile in sorted(self._state.tiles.items()):
            if tile.terrain != "city" or tile.city_owner_id != self._state.current_player:
                continue

            next_points = tile.production_points + CITY_PRODUCTION_PER_TURN
            valid_options = self._city_build_options_for_tile(tile)
            build_choice = tile.build_choice if tile.build_choice in valid_options else DEFAULT_CITY_BUILD
            build_def = UNIT_TYPES[build_choice]
            if next_points >= build_def.production_cost and self._state.get_unit_at(tile.position) is None:
                unit_id = self._state.next_unit_id
                self._state.next_unit_id += 1
                self._state.units[unit_id] = create_unit(unit_id, tile.city_owner_id, build_choice, tile.position)
                next_points -= build_def.production_cost
                messages.append(f"City at {tile.position.to_dict()} produced {build_choice} #{unit_id}.")

            self._state.tiles[key] = tile.__class__(
                position=tile.position,
                terrain=tile.terrain,
                city_owner_id=tile.city_owner_id,
                production_points=next_points,
                build_choice=build_choice,
                city_role=tile.city_role,
            )
        return messages

    def _apply_city_support(self) -> list[str]:
        messages: list[str] = []
        for unit in sorted(self._state.units.values(), key=lambda item: item.unit_id):
            if unit.owner_id != self._state.current_player or unit.embarked_in is not None:
                continue

            unit.moves_remaining = unit.max_moves
            tile = self._state.get_tile(unit.position)
            if tile.terrain != "city" or tile.city_owner_id != self._state.current_player:
                continue

            previous_hp = unit.hp
            repair_amount = CAPITAL_REPAIR_PER_TURN if self._state.city_role(tile.position) == "capital" else CITY_REPAIR_PER_TURN
            unit.hp = min(unit.max_hp, unit.hp + repair_amount)
            if unit.hp > previous_hp:
                messages.append(f"Unit {unit.unit_id} repaired to {unit.hp}/{unit.max_hp} in {self._state.city_role(tile.position)}.")
        return messages

    def _city_build_options_for_tile(self, tile) -> tuple[str, ...]:
        city_role = self._state.city_role(tile.position)
        return CITY_ROLE_BUILD_OPTIONS.get(city_role, CITY_ROLE_BUILD_OPTIONS["city"])

    def _attach_city_build_options(self, state: dict[str, object]) -> None:
        for tile_state in state["tiles"]:
            if tile_state["terrain"] != "city":
                continue
            tile = self._state.get_tile(Position(tile_state["position"]["x"], tile_state["position"]["y"]))
            tile_state["available_build_options"] = list(self._city_build_options_for_tile(tile))

    def _refresh_visibility_memory(self) -> None:
        for player_id in (1, 2):
            visible_positions = self._state.compute_visible_positions(player_id)
            self._state.remember_visible_positions(player_id, visible_positions)

    def _check_capital_victory(self, defeated_player_id: int | None) -> None:
        if defeated_player_id is None:
            return
        for tile in self._state.tiles.values():
            if tile.terrain != "city":
                continue
            if tile.city_owner_id != defeated_player_id:
                continue
            if self._state.city_role(tile.position) == "capital":
                return
        self._state.game_over = True
        self._state.winner_id = self._state.current_player
        self._state.selected_unit_id = None
        self._state.last_event = f"Player {self._state.current_player} captured the last enemy capital and wins."

    def _ensure_game_active(self) -> CommandResult | None:
        if not self._state.game_over:
            return None
        winner_text = f" Player {self._state.winner_id} has already won." if self._state.winner_id is not None else ""
        return self._result(False, f"Game is over.{winner_text}")

    def _result(self, ok: bool, message: str) -> CommandResult:
        return CommandResult(ok=ok, message=message, state=self.get_visible_state())


def create_game(width: int = 20, height: int = 20) -> GameAPI:
    return GameAPI(create_default_state(width=width, height=height))


def create_game_for_scenario(scenario_id: str) -> GameAPI:
    return GameAPI(create_scenario_state(scenario_id))


def load_game(path: str | Path) -> GameAPI:
    source = Path(path)
    state_data = json.loads(source.read_text(encoding="utf-8"))
    return GameAPI(GameState.from_persisted_state(state_data))
