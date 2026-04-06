from __future__ import annotations

import argparse

from game.logic.cli_demo import run_cli_demo


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Empire strategy prototype")
    parser.add_argument(
        "mode",
        nargs="?",
        default="cli",
        choices=("cli", "ui", "capture-demo"),
        help="Run the headless CLI demo, start the Qt/QML UI, or render a short demo video.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.mode == "cli":
        return run_cli_demo()

    if args.mode == "capture-demo":
        from game.ui.demo_capture import render_demo_video

        output_path = render_demo_video()
        print(f"Demo video written to {output_path}")
        return 0

    from game.ui.app import run_ui

    return run_ui()


if __name__ == "__main__":
    raise SystemExit(main())
