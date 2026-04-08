from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from .audio import GameAudio
from .controller import GameController


def run_ui() -> int:
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    controller = GameController()
    audio = GameAudio()
    engine.rootContext().setContextProperty("gameController", controller)
    engine.rootContext().setContextProperty("gameAudio", audio)

    qml_path = Path(__file__).resolve().parent / "qml" / "Main.qml"
    engine.load(str(qml_path))

    if not engine.rootObjects():
        return 1
    return app.exec()
