"""L1s laser rangefinder driver — ASCII protocol over TTL serial."""

import re
import time


def parse_response(text):
    """Parse ASCII response from L1s.

    Returns (distance_m, signal_quality) on success,
    (None, error_code) on measurement error,
    None if the response is unparseable.
    """
    text = text.strip()
    if not text:
        return None

    m = re.match(r'^D=([0-9.]+)m,(\d+)#$', text)
    if m:
        return float(m.group(1)), int(m.group(2))

    m = re.match(r'^E=(\d+)$', text)
    if m:
        return None, int(m.group(1))

    return None


class L1S:
    """L1s laser module serial driver with EN pin control."""

    def __init__(self, port='/dev/serial0', baud=38400, timeout=2.0,
                 en_pin=17):
        import serial
        from gpiozero import DigitalOutputDevice

        self._en = DigitalOutputDevice(en_pin, active_high=True, initial_value=False)
        self._en.on()
        time.sleep(0.7)  # 600 ms startup per datasheet, plus margin
        self._ser = serial.Serial(port, baud, timeout=timeout)
        # Laser is on by default at power-up; confirm and drain multi-line response
        self._send_cmd(b'iLD:1\r\n')

    def _send_cmd(self, cmd):
        """Send command and drain all response lines."""
        self._ser.write(cmd)
        self._ser.timeout = 0.3
        while self._ser.readline():
            pass
        self._ser.timeout = 2.0

    def measure_single(self):
        self._ser.write(b'iSM\r\n')
        line = self._ser.readline().decode('ascii', errors='replace')
        return parse_response(line)

    def laser_on(self):
        self._send_cmd(b'iLD:1\r\n')

    def laser_off(self):
        self._send_cmd(b'iLD:0\r\n')

    def power_on(self):
        self._en.on()
        time.sleep(0.7)  # 600 ms startup time per datasheet

    def power_off(self):
        self._en.off()

    def close(self):
        try:
            self._send_cmd(b'iHALT\r\n')
        except Exception:
            pass
        self._ser.close()
        self._en.close()
