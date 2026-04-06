from __future__ import annotations

from game.logic.api import GameAPI, create_game_for_scenario, load_game
from game.logic.models import MapSize, Position, Tile
from game.logic.rules import create_unit
from game.logic.state import GameState


def make_small_state() -> GameState:
    state = GameState(map_size=MapSize(width=5, height=5))
    for y in range(5):
        for x in range(5):
            state.tiles[(x, y)] = Tile(position=Position(x, y), terrain="plains")
    state.next_unit_id = 10
    return state


def test_land_unit_cannot_enter_water() -> None:
    state = make_small_state()
    state.tiles[(2, 1)] = Tile(position=Position(2, 1), terrain="water")
    state.units = {
        1: create_unit(1, 1, "infantry", Position(1, 1)),
    }
    game = GameAPI(state)

    result = game.move_unit(1, {"x": 2, "y": 1})
    assert result.ok is False
    assert "cannot enter water" in result.message


def test_attacker_can_destroy_defender_and_advance() -> None:
    state = make_small_state()
    state.units = {
        1: create_unit(1, 1, "tank", Position(1, 1)),
        2: create_unit(2, 2, "infantry", Position(2, 1)),
    }
    state.units[2].hp = 4
    game = GameAPI(state)

    result = game.move_unit(1, {"x": 2, "y": 1})

    assert result.ok is True
    assert 2 not in game._state.units
    assert game._state.units[1].position == Position(2, 1)
    assert "destroyed" in result.message


def test_city_is_captured_by_entering_land_unit() -> None:
    state = make_small_state()
    state.tiles[(2, 2)] = Tile(position=Position(2, 2), terrain="city", city_owner_id=2, production_points=0)
    state.units = {
        1: create_unit(1, 1, "infantry", Position(2, 1)),
    }
    game = GameAPI(state)

    result = game.move_unit(1, {"x": 2, "y": 2})

    assert result.ok is True
    assert game._state.tiles[(2, 2)].city_owner_id == 1


def test_city_produces_infantry_when_points_reach_cost() -> None:
    state = make_small_state()
    state.current_player = 2
    state.tiles[(2, 2)] = Tile(position=Position(2, 2), terrain="city", city_owner_id=1, production_points=4)
    state.units = {}
    game = GameAPI(state)

    result = game.end_turn()

    produced_units = [unit for unit in game._state.units.values() if unit.owner_id == 1]
    assert result.ok is True
    assert len(produced_units) == 1
    assert produced_units[0].position == Position(2, 2)
    assert "produced infantry" in result.message


def test_city_production_choice_changes_output_unit() -> None:
    state = make_small_state()
    state.current_player = 2
    state.tiles[(2, 2)] = Tile(position=Position(2, 2), terrain="city", city_owner_id=1, production_points=8, build_choice="infantry")
    state.units = {}
    game = GameAPI(state)

    state.current_player = 1
    set_result = game.set_city_production({"x": 2, "y": 2}, "tank")
    assert set_result.ok is True
    state.current_player = 2
    game.end_turn()
    produced_units = [unit for unit in game._state.units.values() if unit.owner_id == 1]
    assert len(produced_units) == 1
    assert produced_units[0].unit_type == "tank"
    assert "produced tank" in game._state.last_event


def test_coastal_city_can_build_transport() -> None:
    state = make_small_state()
    state.current_player = 2
    state.tiles[(2, 2)] = Tile(position=Position(2, 2), terrain="city", city_owner_id=1, production_points=8, build_choice="infantry")
    state.tiles[(2, 3)] = Tile(position=Position(2, 3), terrain="water")
    state.units = {}
    game = GameAPI(state)

    state.current_player = 1
    set_result = game.set_city_production({"x": 2, "y": 2}, "transport")
    state.current_player = 2
    game.end_turn()

    produced_units = [unit for unit in game._state.units.values() if unit.owner_id == 1]
    assert set_result.ok is True
    assert len(produced_units) == 1
    assert produced_units[0].unit_type == "transport"

    visible_state = game.get_visible_state()
    city_tile = next(tile for tile in visible_state["tiles"] if tile["position"] == {"x": 2, "y": 2})
    assert city_tile["city_role"] == "harbor"


def test_inland_owned_city_defaults_to_factory_and_cannot_build_destroyer() -> None:
    state = make_small_state()
    state.tiles[(2, 2)] = Tile(position=Position(2, 2), terrain="city", city_owner_id=1, production_points=0, build_choice="infantry")
    state.units = {}
    game = GameAPI(state)

    result = game.set_city_production({"x": 2, "y": 2}, "destroyer")

    assert result.ok is False
    assert "not a valid build" in result.message

    visible_state = game.get_visible_state()
    city_tile = next(tile for tile in visible_state["tiles"] if tile["position"] == {"x": 2, "y": 2})
    assert city_tile["city_role"] == "factory"
    assert city_tile["available_build_options"] == ["infantry", "tank"]


def test_explicit_harbor_role_controls_build_options() -> None:
    state = make_small_state()
    state.tiles[(2, 2)] = Tile(
        position=Position(2, 2),
        terrain="city",
        city_owner_id=1,
        production_points=0,
        build_choice="infantry",
        city_role="harbor",
    )
    state.units = {}
    game = GameAPI(state)

    result = game.set_city_production({"x": 2, "y": 2}, "destroyer")

    assert result.ok is True
    assert game._state.tiles[(2, 2)].city_role == "harbor"


def test_explicit_factory_role_can_build_tank_but_not_destroyer() -> None:
    state = make_small_state()
    state.tiles[(2, 2)] = Tile(
        position=Position(2, 2),
        terrain="city",
        city_owner_id=1,
        production_points=0,
        build_choice="tank",
        city_role="factory",
    )
    state.units = {}
    game = GameAPI(state)

    tank_result = game.set_city_production({"x": 2, "y": 2}, "tank")
    destroyer_result = game.set_city_production({"x": 2, "y": 2}, "destroyer")
    visible_state = game.get_visible_state()
    city_tile = next(tile for tile in visible_state["tiles"] if tile["position"] == {"x": 2, "y": 2})

    assert tank_result.ok is True
    assert destroyer_result.ok is False
    assert city_tile["city_role"] == "factory"
    assert city_tile["available_build_options"] == ["infantry", "tank"]


def test_capital_role_extends_vision_range() -> None:
    state = make_small_state()
    state.tiles[(2, 2)] = Tile(
        position=Position(2, 2),
        terrain="city",
        city_owner_id=1,
        production_points=0,
        build_choice="tank",
        city_role="capital",
    )
    state.units = {}
    game = GameAPI(state)

    visible_positions = game._state.compute_visible_positions(1)

    assert (2, 2) in visible_positions
    assert (2, 0) in visible_positions
    assert (0, 2) in visible_positions


def test_units_regain_movement_on_their_turn() -> None:
    state = make_small_state()
    state.current_player = 1
    state.units = {
        1: create_unit(1, 2, "tank", Position(1, 1)),
    }
    state.units[1].moves_remaining = 0
    game = GameAPI(state)

    result = game.end_turn()

    assert result.ok is True
    assert game._state.current_player == 2
    assert game._state.units[1].moves_remaining == game._state.units[1].max_moves


def test_unit_repairs_in_owned_city_at_turn_start() -> None:
    state = make_small_state()
    state.current_player = 1
    state.tiles[(2, 2)] = Tile(position=Position(2, 2), terrain="city", city_owner_id=2, production_points=0, build_choice="infantry")
    state.units = {
        1: create_unit(1, 2, "infantry", Position(2, 2)),
    }
    state.units[1].hp = 5
    state.units[1].moves_remaining = 0
    game = GameAPI(state)

    result = game.end_turn()

    assert result.ok is True
    assert game._state.units[1].hp == 8
    assert game._state.units[1].moves_remaining == game._state.units[1].max_moves
    assert "repaired" in result.message


def test_unit_repairs_more_in_capital_at_turn_start() -> None:
    state = make_small_state()
    state.current_player = 1
    state.tiles[(2, 2)] = Tile(
        position=Position(2, 2),
        terrain="city",
        city_owner_id=2,
        production_points=0,
        build_choice="tank",
        city_role="capital",
    )
    state.units = {
        1: create_unit(1, 2, "tank", Position(2, 2)),
    }
    state.units[1].hp = 5
    state.units[1].moves_remaining = 0
    game = GameAPI(state)

    result = game.end_turn()

    assert result.ok is True
    assert game._state.units[1].hp == 10
    assert "capital" in result.message


def test_visible_state_hides_enemy_units_outside_vision() -> None:
    state = make_small_state()
    state.units = {
        1: create_unit(1, 1, "infantry", Position(1, 1)),
        2: create_unit(2, 2, "infantry", Position(4, 4)),
    }
    game = GameAPI(state)

    visible_state = game.get_visible_state()
    unit_ids = [unit["id"] for unit in visible_state["units"]]

    assert 1 in unit_ids
    assert 2 not in unit_ids


def test_explored_tiles_remain_known_after_turn_changes() -> None:
    state = make_small_state()
    state.units = {
        1: create_unit(1, 1, "infantry", Position(1, 1)),
        2: create_unit(2, 2, "infantry", Position(4, 4)),
    }
    game = GameAPI(state)

    initial_state = game.get_visible_state()
    explored_before = next(tile for tile in initial_state["tiles"] if tile["position"] == {"x": 3, "y": 1})
    assert explored_before["visible"] is True

    game.move_unit(1, {"x": 1, "y": 2})

    later_state = game.get_visible_state()
    explored_after = next(tile for tile in later_state["tiles"] if tile["position"] == {"x": 3, "y": 1})
    assert explored_after["explored"] is True
    assert explored_after["visible"] is False


def test_land_unit_can_embark_on_friendly_transport() -> None:
    state = make_small_state()
    state.tiles[(2, 1)] = Tile(position=Position(2, 1), terrain="water")
    state.units = {
        1: create_unit(1, 1, "infantry", Position(1, 1)),
        2: create_unit(2, 1, "transport", Position(2, 1)),
    }
    game = GameAPI(state)

    result = game.move_unit(1, {"x": 2, "y": 1})

    assert result.ok is True
    assert game._state.units[1].embarked_in == 2
    assert game._state.units[2].cargo_unit_ids == [1]
    assert "embarked" in result.message


def test_embarked_unit_can_disembark_to_adjacent_land() -> None:
    state = make_small_state()
    state.tiles[(2, 1)] = Tile(position=Position(2, 1), terrain="water")
    state.units = {
        1: create_unit(1, 1, "infantry", Position(1, 1)),
        2: create_unit(2, 1, "transport", Position(2, 1)),
    }
    game = GameAPI(state)
    game.move_unit(1, {"x": 2, "y": 1})
    game._state.units[2].moves_remaining = 2

    result = game.move_unit(1, {"x": 3, "y": 1})

    assert result.ok is True
    assert game._state.units[1].embarked_in is None
    assert game._state.units[1].position == Position(3, 1)
    assert game._state.units[2].cargo_unit_ids == []
    assert "disembarked" in result.message


def test_transport_move_keeps_cargo_position_in_sync() -> None:
    state = make_small_state()
    state.tiles[(2, 1)] = Tile(position=Position(2, 1), terrain="water")
    state.tiles[(3, 1)] = Tile(position=Position(3, 1), terrain="water")
    state.units = {
        1: create_unit(1, 1, "infantry", Position(1, 1)),
        2: create_unit(2, 1, "transport", Position(2, 1)),
    }
    game = GameAPI(state)
    game.move_unit(1, {"x": 2, "y": 1})
    game._state.units[2].moves_remaining = 3

    result = game.move_unit(2, {"x": 3, "y": 1})

    assert result.ok is True
    assert game._state.units[2].position == Position(3, 1)
    assert game._state.units[1].position == Position(3, 1)


def test_unit_can_move_to_distant_reachable_target() -> None:
    state = make_small_state()
    state.units = {
        1: create_unit(1, 1, "tank", Position(1, 1)),
    }
    game = GameAPI(state)

    result = game.move_unit(1, {"x": 3, "y": 1})

    assert result.ok is True
    assert game._state.units[1].position == Position(3, 1)
    assert game._state.units[1].moves_remaining == 0


def test_unit_moves_partway_toward_distant_target_when_range_is_insufficient() -> None:
    state = make_small_state()
    state.units = {
        1: create_unit(1, 1, "tank", Position(1, 1)),
    }
    game = GameAPI(state)

    result = game.move_unit(1, {"x": 4, "y": 1})

    assert result.ok is True
    assert game._state.units[1].position == Position(3, 1)
    assert "toward" in result.message


def test_preview_path_matches_reachable_remote_route() -> None:
    state = make_small_state()
    state.units = {
        1: create_unit(1, 1, "tank", Position(1, 1)),
    }
    game = GameAPI(state)

    preview_path = game.get_preview_path(unit_id=1, target=Position(4, 1))
    preview_data = game.get_preview_data(unit_id=1, target=Position(4, 1))

    assert preview_path == [{"x": 2, "y": 1}, {"x": 3, "y": 1}]
    assert preview_data["full_path"] == [{"x": 2, "y": 1}, {"x": 3, "y": 1}, {"x": 4, "y": 1}]
    assert preview_data["stop_position"] == {"x": 3, "y": 1}
    assert preview_data["reaches_target"] is False


def test_visible_state_contains_legal_targets_for_selected_unit() -> None:
    state = make_small_state()
    state.units = {
        1: create_unit(1, 1, "infantry", Position(1, 1)),
        2: create_unit(2, 2, "infantry", Position(2, 1)),
    }
    game = GameAPI(state)
    game.select_unit(1)

    visible_state = game.get_visible_state()
    targets = {(item["position"]["x"], item["position"]["y"]): item["action_type"] for item in visible_state["legal_targets"]}

    assert targets[(2, 1)] == "attack"
    assert targets[(1, 2)] == "move"


def test_embarked_unit_legal_targets_only_show_disembark_tiles() -> None:
    state = make_small_state()
    state.tiles[(2, 1)] = Tile(position=Position(2, 1), terrain="water")
    state.units = {
        1: create_unit(1, 1, "infantry", Position(1, 1)),
        2: create_unit(2, 1, "transport", Position(2, 1)),
    }
    game = GameAPI(state)
    game.move_unit(1, {"x": 2, "y": 1})
    game._state.units[2].moves_remaining = 2
    game.select_unit(1)

    visible_state = game.get_visible_state()
    action_types = {item["action_type"] for item in visible_state["legal_targets"]}

    assert action_types == {"disembark"}
    assert len(visible_state["legal_targets"]) >= 1


def test_save_and_load_roundtrip_preserves_state(tmp_path) -> None:
    state = make_small_state()
    state.tiles[(2, 1)] = Tile(position=Position(2, 1), terrain="water")
    state.tiles[(2, 2)] = Tile(
        position=Position(2, 2),
        terrain="city",
        city_owner_id=1,
        production_points=3,
        build_choice="transport",
        city_role="harbor",
    )
    state.units = {
        1: create_unit(1, 1, "infantry", Position(1, 1)),
        2: create_unit(2, 1, "transport", Position(2, 1)),
    }
    game = GameAPI(state)
    game.move_unit(1, {"x": 2, "y": 1})
    game._state.turn_number = 3
    game._state.last_event = "Custom event."
    game._state.remember_visible_positions(1, {(0, 0), (1, 1)})

    save_path = tmp_path / "save.json"
    game.save_to_file(save_path)
    loaded_game = load_game(save_path)

    assert loaded_game._state.turn_number == 3
    assert loaded_game._state.last_event == "Custom event."
    assert loaded_game._state.units[1].embarked_in == 2
    assert loaded_game._state.units[2].cargo_unit_ids == [1]
    assert (0, 0) in loaded_game._state.explored_tiles_by_player[1]
    assert loaded_game._state.tiles[(2, 2)].city_role == "harbor"
    assert loaded_game._state.tiles[(2, 2)].build_choice == "transport"


def test_city_capture_preserves_city_role() -> None:
    state = make_small_state()
    state.tiles[(2, 2)] = Tile(
        position=Position(2, 2),
        terrain="city",
        city_owner_id=2,
        production_points=0,
        build_choice="transport",
        city_role="harbor",
    )
    state.units = {
        1: create_unit(1, 1, "infantry", Position(2, 1)),
    }
    game = GameAPI(state)

    result = game.move_unit(1, {"x": 2, "y": 2})

    assert result.ok is True
    assert game._state.tiles[(2, 2)].city_owner_id == 1
    assert game._state.tiles[(2, 2)].city_role == "harbor"


def test_capturing_last_enemy_capital_ends_game() -> None:
    state = make_small_state()
    state.tiles[(2, 2)] = Tile(
        position=Position(2, 2),
        terrain="city",
        city_owner_id=2,
        production_points=0,
        build_choice="tank",
        city_role="capital",
    )
    state.units = {
        1: create_unit(1, 1, "infantry", Position(2, 1)),
    }
    game = GameAPI(state)

    result = game.move_unit(1, {"x": 2, "y": 2})

    assert result.ok is True
    assert game._state.game_over is True
    assert game._state.winner_id == 1
    assert "wins" in result.message


def test_named_scenario_can_be_created() -> None:
    game = create_game_for_scenario("frontline")

    assert game._state.map_size.width == 18
    assert game._state.map_size.height == 16
    assert len(game._state.units) >= 4
    assert "Frontline" in game._state.last_event
    city_roles = {tile.city_role for tile in game._state.tiles.values() if tile.terrain == "city"}
    assert city_roles <= {"city", "harbor", "factory", "capital"}
    assert "capital" in city_roles
    capital_count = sum(1 for tile in game._state.tiles.values() if tile.terrain == "city" and tile.city_role == "capital")
    assert capital_count == 2
