from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Property, Signal, Slot

from game.logic import GameAPI, create_game, create_game_for_scenario, list_scenarios, load_game

class GameController(QObject):
    stateChanged = Signal()
    commandMessageChanged = Signal()
    selectedScenarioChanged = Signal()

    def __init__(self, game: GameAPI | None = None) -> None:
        super().__init__()
        self._save_path = Path.cwd() / "saves" / "quicksave.json"
        self._scenarios: list[dict[str, Any]] = list_scenarios()
        self._selected_scenario_id = self._scenarios[0]["id"]
        self._game = game or create_game()
        self._state: dict[str, Any] = self._game.get_visible_state()
        self._command_message = "Ready."

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

    @Slot(int)
    def selectUnit(self, unit_id: int) -> None:
        self._apply_result(self._game.select_unit(unit_id).to_dict())

    @Slot(int, int, int)
    def moveUnit(self, unit_id: int, x: int, y: int) -> None:
        self._apply_result(self._game.move_unit(unit_id, {"x": x, "y": y}).to_dict())

    @Slot()
    def endTurn(self) -> None:
        self._apply_result(self._game.end_turn().to_dict())

    @Slot()
    def startNewGame(self) -> None:
        self._game = create_game_for_scenario(self._selected_scenario_id)
        self._state = self._game.get_visible_state()
        self._command_message = f"New game created: {self._selected_scenario_id}."
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
        self.stateChanged.emit()
        self.commandMessageChanged.emit()

    @Slot(int, int, str)
    def setCityProduction(self, x: int, y: int, unit_type: str) -> None:
        self._apply_result(self._game.set_city_production({"x": x, "y": y}, unit_type).to_dict())

    def _apply_result(self, result: dict[str, Any]) -> None:
        self._state = result["state"]
        self._command_message = result["message"]
        self.stateChanged.emit()
        self.commandMessageChanged.emit()
