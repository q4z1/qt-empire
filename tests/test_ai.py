"""Tests for the AI player."""
from __future__ import annotations

import pytest

from game.logic import GameAPI
from game.logic.ai import AIPlayer
from game.logic.models import Position
from game.logic.rules import create_unit
from game.logic.scenarios import create_scenario_state
from game.logic.state import GameState
from game.logic.models import MapSize
from game.logic.scenarios import _base_state  # type: ignore[attr-defined]
from game.logic.rules import create_unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def minimal_state(width: int = 6, height: int = 6) -> GameState:
    """3×3 plains map with one city per player."""
    state = create_scenario_state("frontline", width=width, height=height)
    return state


def make_api(state: GameState) -> GameAPI:
    return GameAPI(state)


# ---------------------------------------------------------------------------
# AI takes a full turn without crashing
# ---------------------------------------------------------------------------

def test_ai_take_turn_does_not_crash():
    api = make_api(create_scenario_state("classic"))
    # Player 1 ends their turn so Player 2 is active
    api.end_turn()
    ai = AIPlayer(player_id=2)
    ai.take_turn(api)
    # After AI turn, it's player 1's turn again
    visible = api.get_visible_state()
    assert visible["turn"]["current_player"] == 1


def test_ai_take_turn_all_scenarios():
    for scenario_id in ("classic", "islands", "frontline"):
        api = make_api(create_scenario_state(scenario_id))
        api.end_turn()
        ai = AIPlayer(player_id=2)
        ai.take_turn(api)
        visible = api.get_visible_state()
        assert visible["turn"]["current_player"] == 1


# ---------------------------------------------------------------------------
# AI sets production for own cities
# ---------------------------------------------------------------------------

def test_ai_sets_production_for_own_cities():
    api = make_api(create_scenario_state("classic"))
    state = api._state  # player 1's turn — player 2 cities may have no build_choice yet

    # Manually clear build choices on player 2 cities to simulate fresh state
    from game.logic.models import Tile
    for key, tile in list(state.tiles.items()):
        if tile.terrain == "city" and tile.city_owner_id == 2:
            state.tiles[key] = Tile(
                position=tile.position,
                terrain=tile.terrain,
                city_owner_id=tile.city_owner_id,
                production_points=tile.production_points,
                build_choice=None,
                city_role=tile.city_role,
            )

    cities_without_build = [
        t for t in state.tiles.values()
        if t.terrain == "city" and t.city_owner_id == 2 and t.build_choice is None
    ]
    assert cities_without_build, "Test prerequisite: player 2 must have a city without build choice after manual clear"

    # Switch to player 2 so set_city_production is allowed
    state.current_player = 2

    ai = AIPlayer(player_id=2)
    ai._set_production(state, api)

    remaining = [
        t for t in state.tiles.values()
        if t.terrain == "city" and t.city_owner_id == 2 and t.build_choice is None
    ]
    assert len(remaining) == 0


# ---------------------------------------------------------------------------
# AI moves units
# ---------------------------------------------------------------------------

def test_ai_units_move_toward_targets():
    api = make_api(create_scenario_state("frontline"))
    state = api._state
    api.end_turn()  # player 2's turn

    # Record initial positions of player 2 units
    initial_positions = {
        uid: u.position
        for uid, u in state.units.items()
        if u.owner_id == 2 and u.embarked_in is None
    }

    ai = AIPlayer(player_id=2)
    ai._move_all_units(state, api)

    moved = sum(
        1 for uid, old_pos in initial_positions.items()
        if uid in state.units and state.units[uid].position != old_pos
    )
    # At least one unit should have moved (map is small enough for contacts)
    assert moved >= 1


# ---------------------------------------------------------------------------
# AI does not move units belonging to player 1
# ---------------------------------------------------------------------------

def test_ai_only_moves_own_units():
    api = make_api(create_scenario_state("classic"))
    state = api._state
    api.end_turn()  # player 2

    initial_p1_positions = {
        uid: u.position
        for uid, u in state.units.items()
        if u.owner_id == 1 and u.embarked_in is None
    }

    ai = AIPlayer(player_id=2)
    ai._move_all_units(state, api)

    for uid, old_pos in initial_p1_positions.items():
        if uid in state.units:
            assert state.units[uid].position == old_pos, (
                f"AI moved player 1 unit {uid}"
            )


# ---------------------------------------------------------------------------
# AI skips turn if not the current player
# ---------------------------------------------------------------------------

def test_ai_noop_when_not_current_player():
    api = make_api(create_scenario_state("classic"))
    # Player 1 is active; AI plays player 2
    initial_turn = api._state.turn_number

    ai = AIPlayer(player_id=2)
    ai.take_turn(api)  # should be a no-op

    assert api._state.turn_number == initial_turn


# ---------------------------------------------------------------------------
# Multiple consecutive AI turns (end_turn loop)
# ---------------------------------------------------------------------------

def test_ai_survives_multiple_turns():
    api = make_api(create_scenario_state("frontline"))
    ai = AIPlayer(player_id=2)
    for _ in range(6):
        if api._state.game_over:
            break
        # Player 1 passes
        api.end_turn()
        if api._state.current_player == 2:
            ai.take_turn(api)
    # Game must still be in a valid state (no crash, turn counter advanced)
    visible = api.get_visible_state()
    assert visible["turn"]["number"] >= 2
