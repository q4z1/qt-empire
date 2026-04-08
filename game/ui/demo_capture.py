from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from .audio import GameAudio, MOVEMENT_SOUND_FILES, battle_sound_duration_ms, battle_sound_file
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
    audio = GameAudio(enabled=False)
    engine.rootContext().setContextProperty("gameController", controller)
    engine.rootContext().setContextProperty("gameAudio", audio)

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
        elapsed_seconds = 0.0
        sound_events: list[tuple[float, float, str]] = []

        def note_battle_sound(domain: str, unit_type: str, duration_ms: int) -> None:
            if duration_ms <= 0:
                duration_ms = battle_sound_duration_ms(unit_type, domain)
            sound_events.append((elapsed_seconds, duration_ms / 1000.0, battle_sound_file(unit_type, domain)))

        controller.battleSoundRequested.connect(note_battle_sound)

        def capture(seconds: float) -> None:
            nonlocal frame_index, elapsed_seconds
            frame_count = max(1, int(round(seconds * fps)))
            for _ in range(frame_count):
                _settle(app)
                pixmap = root.screen().grabWindow(root.winId())
                if pixmap.isNull():
                    raise RuntimeError("Failed to capture window frame.")
                frame_path = frames_dir / f"frame-{frame_index:04d}.png"
                pixmap.save(str(frame_path))
                frame_index += 1
            elapsed_seconds += seconds

        def pause(seconds: float) -> None:
            capture(seconds)

        def preview(x: int, y: int, seconds: float) -> None:
            controller.setPreviewTarget(x, y)
            capture(seconds)
            controller.clearPreviewTarget()

        def note_movement_sound(unit_id: int, duration_ms: int) -> None:
            unit = _unit_by_id(controller.state, unit_id)
            if unit is None:
                return
            sound_file = MOVEMENT_SOUND_FILES.get(str(unit.get("unit_type", "")))
            if sound_file is None or duration_ms <= 0:
                return
            sound_events.append((elapsed_seconds, duration_ms / 1000.0, sound_file))

        def select_unit(unit_id: int, seconds: float = 0.9) -> None:
            controller.selectUnit(unit_id)
            capture(seconds)

        def move_unit(unit_id: int, x: int, y: int, preview_seconds: float = 1.3, settle_seconds: float = 1.1) -> None:
            select_unit(unit_id, 0.8)
            preview(x, y, preview_seconds)
            controller.moveUnit(unit_id, x, y)
            note_movement_sound(unit_id, int(controller.movementAnimation.get("duration_ms", 0)))
            capture(settle_seconds)

        def end_turn(seconds: float = 1.0) -> None:
            controller.endTurn()
            capture(seconds)

        root.setProperty("currentScreen", "menu")
        pause(1.8)

        controller.setSelectedScenario("frontline")
        pause(1.8)

        pause(1.2)

        controller.startNewGame()
        root.setProperty("currentScreen", "game")
        pause(2.0)

        controller.setCityProduction(2, 8, "artillery")
        pause(1.2)

        move_unit(2, 7, 8, preview_seconds=1.4, settle_seconds=1.4)
        end_turn(1.2)

        move_unit(4, 10, 7, preview_seconds=1.4, settle_seconds=1.4)
        end_turn(1.2)

        move_unit(2, 8, 8, preview_seconds=1.4, settle_seconds=1.4)
        end_turn(1.2)

        move_unit(4, 8, 7, preview_seconds=1.4, settle_seconds=1.4)
        end_turn(1.2)

        select_unit(2)
        pause(0.8)
        preview(8, 7, 1.6)
        controller.moveUnit(2, 8, 7)
        pause(1.9)

        pause(1.6)

        controller.saveGame()
        pause(1.2)

        end_turn(1.2)

        controller.loadGame()
        pause(1.3)

        move_unit(1, 5, 7, preview_seconds=1.4, settle_seconds=1.3)
        end_turn(1.1)

        move_unit(3, 11, 8, preview_seconds=1.4, settle_seconds=1.3)
        end_turn(1.1)

        move_unit(1, 6, 7, preview_seconds=1.4, settle_seconds=1.3)
        end_turn(1.1)

        move_unit(3, 10, 8, preview_seconds=1.4, settle_seconds=1.3)
        end_turn(1.1)

        controller.selectUnit(1)
        pause(0.8)
        preview(7, 7, 1.6)
        controller.moveUnit(1, 7, 7)
        pause(1.8)

        controller.selectUnit(4)
        pause(0.8)
        preview(7, 7, 1.6)
        controller.moveUnit(4, 7, 7)
        pause(1.8)

        end_turn(1.2)

        pause(2.0)

        with tempfile.TemporaryDirectory(prefix="empire-demo-media-") as media_dir_name:
            media_dir = Path(media_dir_name)
            raw_video_path = media_dir / "demo-video.mp4"
            audio_path = media_dir / "demo-audio.wav"
            _encode_video(ffmpeg_path, frames_dir, fps, raw_video_path)
            _render_audio_track(ffmpeg_path, sound_events, elapsed_seconds, audio_path)
            _mux_audio_and_video(ffmpeg_path, raw_video_path, audio_path, target)

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


def _render_audio_track(
    ffmpeg_path: str,
    sound_events: list[tuple[float, float, str]],
    duration_seconds: float,
    target: Path,
) -> None:
    sound_dir = Path(__file__).resolve().parent / "assets" / "sounds"
    event_end_seconds = max((start_seconds + event_duration for start_seconds, event_duration, _sound_file in sound_events), default=0.0)
    audio_duration = max(1.0, duration_seconds, event_end_seconds)

    if not sound_events:
        command = [
            ffmpeg_path,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=r=44100:cl=stereo:d={audio_duration:.3f}",
            "-c:a",
            "pcm_s16le",
            str(target),
        ]
        subprocess.run(command, check=True)
        return

    command: list[str] = [
        ffmpeg_path,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r=44100:cl=stereo:d={audio_duration:.3f}",
    ]
    for _start_seconds, _duration_seconds, sound_file in sound_events:
        command.extend(["-i", str(sound_dir / sound_file)])

    filter_parts = ["[0:a]volume=0[a0]"]
    mix_inputs = ["[a0]"]
    for index, (start_seconds, duration_seconds, _sound_file) in enumerate(sound_events, start=1):
        delay_ms = max(0, int(round(start_seconds * 1000)))
        filter_parts.append(
            f"[{index}:a]aformat=sample_fmts=s16:sample_rates=44100:channel_layouts=stereo,"
            f"atrim=0:{duration_seconds:.3f},asetpts=PTS-STARTPTS,"
            f"adelay={delay_ms}|{delay_ms}[a{index}]"
        )
        mix_inputs.append(f"[a{index}]")

    filter_parts.append("".join(mix_inputs) + f"amix=inputs={len(mix_inputs)}:normalize=0:dropout_transition=0[aout]")

    command.extend([
        "-filter_complex",
        ";".join(filter_parts),
        "-map",
        "[aout]",
        "-c:a",
        "pcm_s16le",
        str(target),
    ])
    subprocess.run(command, check=True)


def _mux_audio_and_video(ffmpeg_path: str, video_path: Path, audio_path: Path, target: Path) -> None:
    command = [
        ffmpeg_path,
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(target),
    ]
    subprocess.run(command, check=True)


def _unit_by_id(state: dict[str, object], unit_id: int) -> dict[str, object] | None:
    for unit in state.get("units", []):
        if int(unit.get("id", -1)) == unit_id:
            return unit
    return None
