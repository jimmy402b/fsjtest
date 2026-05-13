"""Pi Zero 2W data collector — terminal-driven main collection loop."""

import sys
import time
import select
import datetime
import traceback

from .m01 import M01
from .camera import Camera
from .tracker import Tracker
from .storage import Storage


PROMPT = '\n[Enter] capture  [q] quit\n> '


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
        print('Init M01 laser...', end=' ', flush=True)
        m01 = M01()
        print('OK')
        devices['m01'] = m01

        print('Init camera...', end=' ', flush=True)
        camera = Camera()
        print('OK')
        devices['camera'] = camera

        print('Init Vive Tracker...', end=' ', flush=True)
        tracker = Tracker()
        print('OK')
        devices['tracker'] = tracker

        print('Init storage...', end=' ', flush=True)
        storage = Storage()
        print(f'OK\n\nData dir: {storage._session_dir}')

        while True:
            print(PROMPT, end='', flush=True)
            key = wait_for_key()

            if key.lower() == 'q':
                print('\nQuitting.')
                break

            if key not in ('\n', '\r'):
                continue

            # --- capture cycle ---
            ts = time.time()
            timestamp = datetime.datetime.now().isoformat()

            # 1. laser
            print('  Laser...', end=' ', flush=True)
            result = m01.measure_single()
            if result is None:
                print('failed, skipping')
                continue
            distance, signal = result
            print(f'{distance:.3f}m (sig:{signal})')

            # 2. photo
            photo_path = storage._photos_dir / f'{storage._photo_counter + 1:04d}.jpg'
            print('  Photo...', end=' ', flush=True)
            camera.capture(str(photo_path))
            print('OK')

            # 3. pose
            print('  Pose...', end=' ', flush=True)
            pose = tracker.get_pose()
            if pose is None:
                print('no data')
                px = py = pz = rw = rx = ry = rz = None
            else:
                px, py, pz = pose['x'], pose['y'], pose['z']
                rw, rx, ry, rz = pose['qw'], pose['qx'], pose['qy'], pose['qz']
                print(f'({px:.3f},{py:.3f},{pz:.3f})')

            # 4. store
            stored_photo = storage.insert(
                timestamp, distance, signal,
                px, py, pz, rw, rx, ry, rz,
            )
            print(f'  Recorded #{storage._photo_counter}')

    except KeyboardInterrupt:
        print('\n\nInterrupted.')
    finally:
        for name, dev in devices.items():
            try:
                dev.close()
            except Exception:
                pass


if __name__ == '__main__':
    run()
