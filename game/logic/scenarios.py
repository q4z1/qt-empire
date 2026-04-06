from __future__ import annotations

from .models import MapSize, Position, Tile
from .rules import create_unit
from .state import GameState


SCENARIOS: dict[str, dict[str, object]] = {
    "classic": {
        "name": "Classic Strait",
        "description": "Ausgewogene Startkarte mit zentraler Wasserbarriere, Landkampf und erstem Seetransport.",
        "size": {"width": 20, "height": 20},
    },
    "islands": {
        "name": "Island Crossing",
        "description": "Getrennte Inselräume mit mehr Wasser und früher Relevanz fuer Transport und Seewege.",
        "size": {"width": 22, "height": 18},
    },
    "frontline": {
        "name": "Frontline",
        "description": "Kompakteres Landfront-Szenario mit schnellerem Bodenkontakt und wenig Wasser.",
        "size": {"width": 18, "height": 16},
    },
}


def list_scenarios() -> list[dict[str, object]]:
    return [
        {
            "id": scenario_id,
            "name": scenario["name"],
            "description": scenario["description"],
            "width": scenario["size"]["width"],
            "height": scenario["size"]["height"],
        }
        for scenario_id, scenario in SCENARIOS.items()
    ]


def create_default_state(width: int = 20, height: int = 20) -> GameState:
    return create_scenario_state("classic", width=width, height=height)


def create_scenario_state(scenario_id: str, width: int | None = None, height: int | None = None) -> GameState:
    if scenario_id not in SCENARIOS:
        raise KeyError(f"Unknown scenario: {scenario_id}")

    scenario = SCENARIOS[scenario_id]
    scenario_width = width if width is not None else int(scenario["size"]["width"])
    scenario_height = height if height is not None else int(scenario["size"]["height"])

    builders = {
        "classic": _build_classic_strait,
        "islands": _build_islands,
        "frontline": _build_frontline,
    }
    state = builders[scenario_id](scenario_width, scenario_height)
    state.last_event = f"Scenario loaded: {scenario['name']}."
    return state


def _build_classic_strait(width: int, height: int) -> GameState:
    state = _base_state(width, height, terrain_fn=_classic_terrain)
    _set_city_role(state, Position(2, 2), "capital")
    _set_city_role(state, Position(width - 3, height - 3), "capital")
    state.units = {
        1: create_unit(1, 1, "infantry", Position(2, 3)),
        2: create_unit(2, 1, "tank", Position(3, 2)),
        3: create_unit(3, 1, "transport", Position(4, height // 2 - 1)),
        4: create_unit(4, 2, "infantry", Position(width - 3, height - 4)),
        5: create_unit(5, 2, "destroyer", Position(width // 2, height // 2)),
    }
    state.next_unit_id = 6
    return state


def _build_islands(width: int, height: int) -> GameState:
    state = _base_state(width, height, terrain_fn=_island_terrain)
    _set_city_role(state, Position(3, 3), "capital")
    _set_city_role(state, Position(width - 4, height - 4), "capital")
    state.units = {
        1: create_unit(1, 1, "infantry", Position(3, 4)),
        2: create_unit(2, 1, "transport", Position(5, 7)),
        3: create_unit(3, 1, "destroyer", Position(7, 8)),
        4: create_unit(4, 2, "infantry", Position(width - 4, height - 5)),
        5: create_unit(5, 2, "transport", Position(width - 6, height - 8)),
    }
    state.next_unit_id = 6
    return state


def _build_frontline(width: int, height: int) -> GameState:
    state = _base_state(width, height, terrain_fn=_frontline_terrain)
    _set_city_role(state, Position(2, height // 2), "capital")
    _set_city_role(state, Position(width - 3, height // 2 - 1), "capital")
    state.units = {
        1: create_unit(1, 1, "infantry", Position(4, height // 2 - 1)),
        2: create_unit(2, 1, "tank", Position(5, height // 2)),
        3: create_unit(3, 2, "infantry", Position(width - 5, height // 2)),
        4: create_unit(4, 2, "tank", Position(width - 6, height // 2 - 1)),
    }
    state.next_unit_id = 5
    return state


def _base_state(width: int, height: int, terrain_fn) -> GameState:
    state = GameState(map_size=MapSize(width=width, height=height))
    for y in range(height):
        for x in range(width):
            terrain, city_owner_id = terrain_fn(x, y, width, height)
            state.tiles[(x, y)] = Tile(
                position=Position(x, y),
                terrain=terrain,
                city_owner_id=city_owner_id,
                production_points=0,
                build_choice="infantry" if terrain == "city" else None,
                city_role=None,
            )
    for key, tile in list(state.tiles.items()):
        if tile.terrain != "city":
            continue
        city_role = _default_city_role_for_tile(state, tile)
        state.tiles[key] = Tile(
            position=tile.position,
            terrain=tile.terrain,
            city_owner_id=tile.city_owner_id,
            production_points=tile.production_points,
            build_choice=_default_build_choice_for_role(city_role),
            city_role=city_role,
        )
    return state


def _default_city_role_for_tile(state: GameState, tile: Tile) -> str:
    if state.is_coastal_city(tile.position):
        return "harbor"
    if tile.city_owner_id is not None:
        return "factory"
    return "city"


def _default_build_choice_for_role(city_role: str) -> str:
    if city_role == "harbor":
        return "transport"
    if city_role in ("factory", "capital"):
        return "tank"
    return "infantry"


def _set_city_role(state: GameState, position: Position, city_role: str) -> None:
    tile = state.get_tile(position)
    state.tiles[(position.x, position.y)] = Tile(
        position=tile.position,
        terrain=tile.terrain,
        city_owner_id=tile.city_owner_id,
        production_points=tile.production_points,
        build_choice=_default_build_choice_for_role(city_role),
        city_role=city_role,
    )


def _classic_terrain(x: int, y: int, width: int, height: int) -> tuple[str, int | None]:
    if (x, y) == (2, 2):
        return "city", 1
    if (x, y) == (width - 3, height - 3):
        return "city", 2
    coastal_band = y in (height // 2 - 1, height // 2)
    if coastal_band and 3 < x < width - 4:
        return "water", None
    if (x + y) % 11 == 0:
        return "forest", None
    if x in (0, width - 1) or y in (0, height - 1):
        return "mountain", None
    return "plains", None


def _island_terrain(x: int, y: int, width: int, height: int) -> tuple[str, int | None]:
    if x in (0, width - 1) or y in (0, height - 1):
        return "water", None
    if 2 <= x <= 7 and 2 <= y <= 8:
        if (x, y) == (3, 3):
            return "city", 1
        return ("forest", None) if (x + y) % 4 == 0 else ("plains", None)
    if width - 8 <= x <= width - 3 and height - 9 <= y <= height - 3:
        if (x, y) == (width - 4, height - 4):
            return "city", 2
        return ("forest", None) if (x + y) % 5 == 0 else ("plains", None)
    if width // 2 - 2 <= x <= width // 2 + 1 and height // 2 - 1 <= y <= height // 2 + 1:
        return ("city", None) if (x, y) == (width // 2, height // 2) else ("plains", None)
    return "water", None


def _frontline_terrain(x: int, y: int, width: int, height: int) -> tuple[str, int | None]:
    if (x, y) == (2, height // 2):
        return "city", 1
    if (x, y) == (width - 3, height // 2 - 1):
        return "city", 2
    if x in (0, width - 1) or y in (0, height - 1):
        return "mountain", None
    if y == height // 2 + 2 and 4 < x < width - 5:
        return "water", None
    if (x * 2 + y) % 9 == 0:
        return "forest", None
    return "plains", None
