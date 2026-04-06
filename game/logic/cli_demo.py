from __future__ import annotations

import json

from .api import create_game


def run_cli_demo() -> int:
    game = create_game()

    print("Initial state:")
    print(json.dumps(game.get_visible_state(), indent=2))

    print("\nSelect unit 1:")
    print(json.dumps(game.select_unit(1).to_dict(), indent=2))

    print("\nMove unit 1 to (2, 4):")
    print(json.dumps(game.move_unit(1, {"x": 2, "y": 4}).to_dict(), indent=2))

    print("\nEnd turn:")
    print(json.dumps(game.end_turn().to_dict(), indent=2))

    print("\nPlayer 2 attacks tank with infantry:")
    print(json.dumps(game.move_unit(3, {"x": 17, "y": 15}).to_dict(), indent=2))
    return 0
