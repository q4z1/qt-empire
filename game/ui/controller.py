from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Property, Signal, Slot

from game.logic import GameAPI, create_game, create_game_for_scenario, list_scenarios, load_game
from game.logic.models import Position
from .audio import battle_sound_duration_ms

class GameController(QObject):
    stateChanged = Signal()
    commandMessageChanged = Signal()
    selectedScenarioChanged = Signal()
    activeThemeChanged = Signal()
    movementAnimationChanged = Signal()
    battleSoundRequested = Signal(str, str, int)

    def __init__(self, game: GameAPI | None = None) -> None:
        super().__init__()
        self._save_path = Path.cwd() / "saves" / "quicksave.json"
        self._theme_settings_path = Path.cwd() / "saves" / "ui-settings.json"
        self._scenarios: list[dict[str, Any]] = list_scenarios()
        self._selected_scenario_id = self._scenarios[0]["id"]
        self._active_theme_id = self._load_active_theme_id()
        self._game = game or create_game()
        self._state: dict[str, Any] = self._game.get_visible_state()
        self._command_message = "Ready."
        self._movement_animation: dict[str, Any] = self._empty_movement_animation()

    @Property("QVariant", notify=stateChanged)
    def state(self) -> dict[str, Any]:
        return self._state

    @Property(str, notify=commandMessageChanged)
    def commandMessage(self) -> str:
        return self._command_message

    @Property(str, constant=True)
    def savePath(self) -> str:
        return str(self._save_path)

    @Property(str, constant=True)
    def saveDisplayPath(self) -> str:
        return f"{self._save_path.parent.name}/{self._save_path.name}"

    @Property("QVariantList", constant=True)
    def scenarios(self) -> list[dict[str, Any]]:
        return self._scenarios

    @Property(str, notify=selectedScenarioChanged)
    def selectedScenarioId(self) -> str:
        return self._selected_scenario_id

    @Property(str, notify=activeThemeChanged)
    def activeThemeId(self) -> str:
        return self._active_theme_id

    @Property("QVariant", notify=movementAnimationChanged)
    def movementAnimation(self) -> dict[str, Any]:
        return self._movement_animation

    @Slot(int)
    def selectUnit(self, unit_id: int) -> None:
        self._apply_result(self._game.select_unit(unit_id).to_dict())

    @Slot(int, int, int)
    def moveUnit(self, unit_id: int, x: int, y: int) -> None:
        target = Position(x=x, y=y)
        unit = self._find_unit(unit_id)
        action_type = self._action_type_for_target(target)
        movement_animation = self._build_movement_animation(unit_id, target)
        result = self._game.move_unit(unit_id, target).to_dict()
        self._apply_result(result)
        if result["ok"] and movement_animation is not None:
            self._movement_animation = movement_animation
            self.movementAnimationChanged.emit()
        if result["ok"] and action_type == "attack" and unit is not None:
            unit_type = str(unit.get("unit_type", ""))
            domain = str(unit.get("domain", "land"))
            self.battleSoundRequested.emit(domain, unit_type, battle_sound_duration_ms(unit_type, domain))

    @Slot()
    def endTurn(self) -> None:
        self._clear_movement_animation()
        previous_state = self._state
        result = self._game.end_turn().to_dict()
        self._apply_result(result)
        queued_animation = self._build_queued_movement_animation(previous_state, result["state"])
        if queued_animation is not None:
            self._movement_animation = queued_animation
            self.movementAnimationChanged.emit()

    @Slot()
    def startNewGame(self) -> None:
        self._game = create_game_for_scenario(self._selected_scenario_id)
        self._state = self._game.get_visible_state()
        self._command_message = f"New game created: {self._selected_scenario_id}."
        self._clear_movement_animation()
        self.stateChanged.emit()
        self.commandMessageChanged.emit()

    @Slot(str)
    def setSelectedScenario(self, scenario_id: str) -> None:
        if scenario_id == self._selected_scenario_id:
            return
        if scenario_id not in {scenario["id"] for scenario in self._scenarios}:
            return
        self._selected_scenario_id = scenario_id
        self.selectedScenarioChanged.emit()

    @Slot(str)
    def setActiveThemeId(self, theme_id: str) -> None:
        if theme_id == self._active_theme_id:
            return
        if theme_id not in {"classicFlat", "empireDeluxe"}:
            return
        self._active_theme_id = theme_id
        self._save_active_theme_id()
        self.activeThemeChanged.emit()

    @Slot()
    def saveGame(self) -> None:
        saved_path = self._game.save_to_file(self._save_path)
        self._command_message = f"Game saved to {saved_path.name}."
        self.commandMessageChanged.emit()

    @Slot()
    def loadGame(self) -> None:
        if not self._save_path.exists():
            self._command_message = "No save file found."
            self.commandMessageChanged.emit()
            return

        self._game = load_game(self._save_path)
        self._state = self._game.get_visible_state()
        self._command_message = f"Game loaded from {self._save_path.name}."
        self._clear_movement_animation()
        self.stateChanged.emit()
        self.commandMessageChanged.emit()

    @Slot(int, int, str)
    def setCityProduction(self, x: int, y: int, unit_type: str) -> None:
        self._apply_result(self._game.set_city_production({"x": x, "y": y}, unit_type).to_dict())

    @Slot(int)
    def clearUnitOrders(self, unit_id: int) -> None:
        self._apply_result(self._game.clear_unit_orders(unit_id).to_dict())

    @Slot(int, int, int)
    def setPendingMoveTarget(self, unit_id: int, x: int, y: int) -> None:
        self._apply_result(self._game.set_pending_move_target(unit_id, {"x": x, "y": y}).to_dict())

    @Slot(int)
    def clearPendingMoveTarget(self, unit_id: int) -> None:
        self._apply_result(self._game.set_pending_move_target(unit_id, None).to_dict())

    @Slot()
    def clearMovementAnimation(self) -> None:
        self._clear_movement_animation()

    @Slot(int, int)
    def setPreviewTarget(self, x: int, y: int) -> None:
        self._state = self._game.set_preview_target({"x": x, "y": y})
        self.stateChanged.emit()

    @Slot()
    def clearPreviewTarget(self) -> None:
        self._state = self._game.set_preview_target(None)
        self.stateChanged.emit()

    def _apply_result(self, result: dict[str, Any]) -> None:
        self._state = result["state"]
        self._command_message = result["message"]
        self.stateChanged.emit()
        self.commandMessageChanged.emit()

    def _build_movement_animation(self, unit_id: int, target: Position) -> dict[str, Any] | None:
        action_type = self._action_type_for_target(target)
        if action_type in {"attack", "embark", "disembark"}:
            return None

        preview_data = self._game.get_preview_data(unit_id, target)
        path = preview_data["reachable_path"]
        if not path:
            return None

        unit = self._find_unit(unit_id)
        if unit is None:
            return None

        return {
            "active": True,
            "unit_id": unit_id,
            "unit_type": unit["unit_type"],
            "owner_id": unit["owner_id"],
            "origin": unit["position"],
            "path": path,
            "duration_ms": max(220, 180 * len(path)),
        }

    def _build_queued_movement_animation(
        self,
        previous_state: dict[str, Any],
        current_state: dict[str, Any],
    ) -> dict[str, Any] | None:
        previous_units = {unit["id"]: unit for unit in previous_state.get("units", [])}
        current_units = {unit["id"]: unit for unit in current_state.get("units", [])}

        changed_units: list[dict[str, Any]] = []
        for unit_id, current_unit in current_units.items():
            previous_unit = previous_units.get(unit_id)
            if previous_unit is None:
                continue
            if previous_unit.get("queued_destination") is None:
                continue
            if previous_unit.get("position") == current_unit.get("position"):
                continue
            changed_units.append(
                {
                    "id": unit_id,
                    "unit_type": current_unit.get("unit_type", ""),
                    "owner_id": current_unit.get("owner_id", -1),
                    "origin": previous_unit.get("position"),
                    "destination": current_unit.get("position"),
                    "queued_destination": previous_unit.get("queued_destination"),
                }
            )

        if not changed_units:
            return None

        changed_units.sort(key=lambda item: item["id"])
        unit = changed_units[0]
        origin = unit["origin"]
        destination = unit["destination"]
        if not isinstance(origin, dict) or not isinstance(destination, dict):
            return None

        distance = abs(int(origin["x"]) - int(destination["x"])) + abs(int(origin["y"]) - int(destination["y"]))
        if distance <= 0:
            return None

        return {
            "active": True,
            "unit_id": unit["id"],
            "unit_type": unit["unit_type"],
            "owner_id": unit["owner_id"],
            "origin": origin,
            "path": [destination],
            "duration_ms": max(220, 140 * distance),
        }

    def _action_type_for_target(self, target: Position) -> str | None:
        target_dict = target.to_dict()
        for legal_target in self._state.get("legal_targets", []):
            if legal_target.get("position") == target_dict:
                return str(legal_target.get("action_type"))
        return None

    def _find_unit(self, unit_id: int) -> dict[str, Any] | None:
        for unit in self._state.get("units", []):
            if unit.get("id") == unit_id:
                return unit
        return None

    def _clear_movement_animation(self) -> None:
        if self._movement_animation["active"]:
            self._movement_animation = self._empty_movement_animation()
            self.movementAnimationChanged.emit()

    def _empty_movement_animation(self) -> dict[str, Any]:
        return {
            "active": False,
            "unit_id": -1,
            "unit_type": "",
            "owner_id": -1,
            "origin": None,
            "path": [],
            "duration_ms": 0,
        }

    def _load_active_theme_id(self) -> str:
        if not self._theme_settings_path.exists():
            return "empireDeluxe"

        try:
            data = json.loads(self._theme_settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return "empireDeluxe"

        theme_id = data.get("active_theme_id")
        if theme_id in {"classicFlat", "empireDeluxe"}:
            return str(theme_id)
        return "empireDeluxe"

    def _save_active_theme_id(self) -> None:
        self._theme_settings_path.parent.mkdir(parents=True, exist_ok=True)
        self._theme_settings_path.write_text(
            json.dumps({"active_theme_id": self._active_theme_id}, indent=2),
            encoding="utf-8",
        )
