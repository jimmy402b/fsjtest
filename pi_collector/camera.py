"""Picamera2 wrapper — capture and save JPG photos."""

from pathlib import Path


class Camera:
    def __init__(self):
        from picamera2 import Picamera2
        self._cam = Picamera2()
        config = self._cam.create_still_configuration()
        self._cam.configure(config)
        self._cam.start()

    def capture(self, filepath):
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        self._cam.capture_file(str(filepath))

    def close(self):
        self._cam.stop()
