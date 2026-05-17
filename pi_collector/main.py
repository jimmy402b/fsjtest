"""Pi Zero 2W data collector — terminal-driven main collection loop."""

import sys
import time
import select
import subprocess
import threading
import datetime
import os

from .camera import Camera
from .storage import Storage
from .l1s import L1S

PROMPT = '\n[Enter] capture  [q] quit\n> '

POSE_FILE = '/tmp/tracker_pose.txt'


class PoseReader:
    """Reads latest pose from tracker_daemon via shared file."""

    def __init__(self, daemon_path='/home/jimmylin/tracker_daemon'):
        self._latest_pose = None
        self._lock = threading.Lock()
        self._running = True

        # Start daemon writing to file
        cmd = [daemon_path, '-o', POSE_FILE]
        if os.geteuid() != 0:
            cmd = ['sudo', '-n'] + cmd

        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(0.5)
        if self._proc.poll() is not None:
            raise RuntimeError(f'tracker_daemon exited early (rc={self._proc.returncode})')

        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self):
        pos = 0
        while self._running:
            try:
                with open(POSE_FILE, 'r') as f:
                    f.seek(pos)
                    for line in f:
                        if not self._running:
                            break
                        if line.startswith('WM0'):
                            parts = line.strip().split()
                            if len(parts) >= 8:
                                with self._lock:
                                    self._latest_pose = {
                                        'x': float(parts[1]),
                                        'y': float(parts[2]),
                                        'z': float(parts[3]),
                                        'qw': float(parts[4]),
                                        'qx': float(parts[5]),
                                        'qy': float(parts[6]),
                                        'qz': float(parts[7]),
                                    }
                    pos = f.tell()
            except FileNotFoundError:
                pass
            time.sleep(0.05)

    def get_pose(self):
        with self._lock:
            return self._latest_pose

    def close(self):
        self._running = False
        self._proc.terminate()
        try:
            self._proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._proc.kill()


def wait_for_key():
    """Block until a keypress on stdin, return the character."""
    while True:
        if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
            return sys.stdin.read(1)


def run():
    print('=' * 50)
    print('Pi Zero 2W Lab Data Collector')
    print('=' * 50)

    devices = {}

    try:
        # --- Tracker ---
        print('Starting tracker daemon...', end=' ', flush=True)
        pose_reader = PoseReader()
        print('OK')
        devices['pose_reader'] = pose_reader

        # --- Camera ---
        print('Init camera...', end=' ', flush=True)
        camera = Camera()
        print('OK')
        devices['camera'] = camera

        # --- Storage ---
        print('Init storage...', end=' ', flush=True)
        storage = Storage()
        print(f'OK\n\nData dir: {storage._session_dir}')

        # --- Laser ---
        print('Init laser...', end=' ', flush=True)
        laser = L1S()
        print('OK')
        devices['laser'] = laser

        # --- Wait for first pose ---
        print('Waiting for pose lock...', end=' ', flush=True)
        for _ in range(300):  # 30 second timeout
            if pose_reader.get_pose() is not None:
                print('LOCKED')
                break
            time.sleep(0.1)
        else:
            print('timeout — pose may not be available')

        # --- Main loop ---
        while True:
            print(PROMPT, end='', flush=True)
            key = wait_for_key()

            if key.lower() == 'q':
                print('\nQuitting.')
                break

            if key not in ('\n', '\r'):
                continue

            # --- capture cycle ---
            timestamp = datetime.datetime.now().isoformat()

            # 1. Pose
            print('  Pose...', end=' ', flush=True)
            pose = pose_reader.get_pose()
            if pose is None:
                print('no data, skipping')
                continue
            print(f'({pose["x"]:.3f},{pose["y"]:.3f},{pose["z"]:.3f})')

            # 2. Laser
            print('  Laser...', end=' ', flush=True)
            distance_m = None
            signal_quality = None
            result = laser.measure_single()
            if result is not None:
                distance_m, signal_quality = result
                if distance_m is not None:
                    print(f'{distance_m:.3f}m sig={signal_quality}')
                else:
                    print(f'error E={signal_quality}')
            else:
                print('no response')

            # 3. Photo
            photo_path = storage._photos_dir / f'{storage._photo_counter + 1:04d}.jpg'
            print('  Photo...', end=' ', flush=True)
            camera.capture(str(photo_path))
            print('OK')

            # 4. Store
            storage.insert(
                timestamp, distance_m, signal_quality,
                pose['x'], pose['y'], pose['z'],
                pose['qw'], pose['qx'], pose['qy'], pose['qz'],
            )
            print(f'  Recorded #{storage._photo_counter}')

    except KeyboardInterrupt:
        print('\n\nInterrupted.')
    except Exception as e:
        print(f'\nError: {e}')
        import traceback
        traceback.print_exc()
    finally:
        for name, dev in devices.items():
            try:
                dev.close()
            except Exception:
                pass


if __name__ == '__main__':
    run()
