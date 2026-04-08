from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QTimer, QUrl, Slot
from PySide6.QtMultimedia import QSoundEffect


MOVEMENT_SOUND_FILES: dict[str, str] = {
    "infantry": "infantry-footsteps-loop.wav",
    "tank": "tracked-vehicle.wav",
    "artillery": "tracked-vehicle.wav",
    "transport": "ship-engine.wav",
    "destroyer": "ship-engine.wav",
}

BATTLE_SOUND_FILES: dict[str, str] = {
    "land": "battle-ground-explosion.wav",
    "air": "battle-air-flyby.wav",
    "sea": "battle-sea-destroyer.wav",
}

BATTLE_SOUND_DURATIONS_MS: dict[str, int] = {
    "land": 1100,
    "air": 1600,
    "sea": 1400,
}

_BATTLE_UNIT_TYPE_OVERRIDES: dict[str, str] = {
    "fighter": "air",
    "bomber": "air",
    "helicopter": "air",
    "jet": "air",
    "plane": "air",
    "destroyer": "sea",
}


def battle_sound_key(unit_type: str, domain: str) -> str:
    key = _BATTLE_UNIT_TYPE_OVERRIDES.get(unit_type.lower())
    if key is not None:
        return key
    if domain in BATTLE_SOUND_FILES:
        return domain
    return "land"


def battle_sound_file(unit_type: str, domain: str) -> str:
    return BATTLE_SOUND_FILES[battle_sound_key(unit_type, domain)]


def battle_sound_duration_ms(unit_type: str, domain: str) -> int:
    return BATTLE_SOUND_DURATIONS_MS[battle_sound_key(unit_type, domain)]


class GameAudio(QObject):
    def __init__(self, enabled: bool = True) -> None:
        super().__init__()
        self._enabled = enabled
        self._sound_dir = Path(__file__).resolve().parent / "assets" / "sounds"
        self._effects: dict[str, QSoundEffect] = {}
        self._active_effect: QSoundEffect | None = None
        self._stop_timer = QTimer(self)
        self._stop_timer.setSingleShot(True)
        self._stop_timer.timeout.connect(self._stop_active_effect)
        if not self._enabled:
            return

        for sound_file in sorted(set(MOVEMENT_SOUND_FILES.values()) | set(BATTLE_SOUND_FILES.values())):
            path = self._sound_dir / sound_file
            if not path.exists():
                continue
            effect = QSoundEffect(self)
            effect.setSource(QUrl.fromLocalFile(str(path)))
            effect.setLoopCount(1)
            effect.setVolume(0.55)
            self._effects[sound_file] = effect

    @Slot(str, int)
    def playMovement(self, unit_type: str, duration_ms: int = 0) -> None:
        if not self._enabled:
            return

        sound_file = MOVEMENT_SOUND_FILES.get(unit_type)
        if sound_file is None:
            return

        effect = self._effects.get(sound_file)
        if effect is None:
            return

        self._stop_timer.stop()
        self._stop_active_effect()

        self._active_effect = effect
        effect.play()
        if duration_ms > 0:
            self._stop_timer.start(duration_ms)

    @Slot(str, str, int)
    def playBattle(self, domain: str, unit_type: str = "", duration_ms: int = 0) -> None:
        if not self._enabled:
            return

        sound_file = battle_sound_file(unit_type, domain)
        effect = self._effects.get(sound_file)
        if effect is None:
            return

        self._stop_timer.stop()
        self._stop_active_effect()

        self._active_effect = effect
        effect.play()
        if duration_ms <= 0:
            duration_ms = battle_sound_duration_ms(unit_type, domain)
        if duration_ms > 0:
            self._stop_timer.start(duration_ms)

    def _stop_active_effect(self) -> None:
        if self._active_effect is None:
            return

        self._active_effect.stop()
        self._active_effect = None
