"""SQLite storage and photo file manager."""

import sqlite3
from datetime import datetime
from pathlib import Path


class Storage:
    def __init__(self, base_dir='data'):
        session_name = datetime.now().strftime('session_%Y%m%d_%H%M%S')
        self._session_dir = Path(base_dir) / session_name
        self._photos_dir = self._session_dir / 'photos'
        self._photos_dir.mkdir(parents=True, exist_ok=True)
        self._photo_counter = 0

        db_path = self._session_dir / 'collect.db'
        self._conn = sqlite3.connect(str(db_path))
        self._conn.execute('''
            CREATE TABLE measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                distance_m REAL,
                signal_quality INTEGER,
                photo_path TEXT,
                pos_x REAL, pos_y REAL, pos_z REAL,
                rot_w REAL, rot_x REAL, rot_y REAL, rot_z REAL
            )
        ''')
        self._conn.commit()

    def insert(self, timestamp, distance_m, signal_quality,
               pos_x, pos_y, pos_z, rot_w, rot_x, rot_y, rot_z):
        self._photo_counter += 1
        photo_path = f'photos/{self._photo_counter:04d}.jpg'

        self._conn.execute('''
            INSERT INTO measurements
                (timestamp, distance_m, signal_quality, photo_path,
                 pos_x, pos_y, pos_z, rot_w, rot_x, rot_y, rot_z)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, distance_m, signal_quality, photo_path,
              pos_x, pos_y, pos_z, rot_w, rot_x, rot_y, rot_z))
        self._conn.commit()

        return str(self._photos_dir / f'{self._photo_counter:04d}.jpg')

    def close(self):
        self._conn.close()
