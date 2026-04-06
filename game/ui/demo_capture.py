from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from .controller import GameController


def render_demo_video(output_path: str | Path | None = None, fps: int = 8) -> Path:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        raise RuntimeError("ffmpeg is required to render the demo video.")

    target = Path(output_path) if output_path is not None else Path.cwd() / "captures" / "demo-launcher-ingame.mp4"
    target.parent.mkdir(parents=True, exist_ok=True)

    app = QGuiApplication([])
    engine = QQmlApplicationEngine()
    controller = GameController()
    engine.rootContext().setContextProperty("gameController", controller)

    qml_path = Path(__file__).resolve().parent / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        raise RuntimeError("QML failed to load.")

    root = engine.rootObjects()[0]
    root.show()
    _settle(app)

    with tempfile.TemporaryDirectory(prefix="empire-demo-frames-") as frames_dir_name:
        frames_dir = Path(frames_dir_name)
        frame_index = 0

        def capture(seconds: float) -> None:
            nonlocal frame_index
            frame_count = max(1, int(round(seconds * fps)))
            for _ in range(frame_count):
                _settle(app)
                pixmap = root.screen().grabWindow(root.winId())
                if pixmap.isNull():
                    raise RuntimeError("Failed to capture window frame.")
                frame_path = frames_dir / f"frame-{frame_index:04d}.png"
                pixmap.save(str(frame_path))
                frame_index += 1

        root.setProperty("currentScreen", "menu")
        capture(1.2)

        controller.setSelectedScenario("islands")
        capture(1.0)

        controller.startNewGame()
        root.setProperty("currentScreen", "game")
        capture(1.2)

        controller.selectUnit(1)
        capture(0.8)

        controller.moveUnit(1, 4, 4)
        capture(0.8)

        controller.selectUnit(3)
        capture(0.8)

        controller.moveUnit(3, 8, 8)
        capture(0.8)

        controller.saveGame()
        capture(0.8)

        controller.endTurn()
        capture(1.0)

        _encode_video(ffmpeg_path, frames_dir, fps, target)

    app.quit()
    return target


def _settle(app: QGuiApplication) -> None:
    for _ in range(3):
        app.processEvents()
        time.sleep(0.03)


def _encode_video(ffmpeg_path: str, frames_dir: Path, fps: int, target: Path) -> None:
    command = [
        ffmpeg_path,
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / "frame-%04d.png"),
        "-vf",
        "format=yuv420p",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "22",
        str(target),
    ]
    subprocess.run(command, check=True)
