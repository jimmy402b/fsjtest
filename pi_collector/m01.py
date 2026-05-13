"""M01 laser rangefinder module — protocol codec (pure functions) + serial driver."""

HEAD = 0xAA

FUNC_MEAS_SINGLE = 0x0020
FUNC_MEAS_CONTINUOUS = 0x0021
FUNC_MEAS_RESULT = 0x0022
FUNC_ERR_CODE = 0x0000
FUNC_BAT_VLTG = 0x0006
FUNC_TEMP = 0x0007
FUNC_HARDWAR_VER = 0x000A
FUNC_SOFTWARE_VER = 0x000C
FUNC_SERIAL_NUM = 0x000E
FUNC_SET_ADDR = 0x0010
FUNC_SET_OFFSET = 0x0012
FUNC_SET_BAUD = 0x0014


def compute_checksum(data):
    return sum(data) & 0xFF


def bcd_to_distance(bcd_value):
    hex_str = f"{bcd_value:08x}"
    return int(hex_str) / 1000.0


def build_command_packet(func_code, addr=0x00, is_read=False, data=None):
    rw_bit = 0x80 if is_read else 0x00
    rw_addr = rw_bit | (addr & 0x7F)
    func_hi = (func_code >> 8) & 0xFF
    func_lo = func_code & 0xFF

    if data is None:
        data = []

    data_count = len(data)
    body = [rw_addr, func_hi, func_lo, data_count] + data
    checksum = compute_checksum(body)
    return bytes([HEAD] + body + [checksum])


def parse_response(raw):
    if len(raw) < 6:
        return None
    if raw[0] != HEAD:
        return None

    data_count = raw[4]
    expected_len = 5 + data_count + 1
    if len(raw) < expected_len:
        return None

    body = raw[1:expected_len - 1]
    actual_checksum = raw[expected_len - 1]
    if compute_checksum(body) != actual_checksum:
        return None

    distance = None
    signal = None

    if data_count >= 4:
        bcd = int.from_bytes(raw[5:9], 'big')
        distance = bcd_to_distance(bcd)

    if data_count >= 6:
        signal = int.from_bytes(raw[9:11], 'big')

    return distance, signal


class M01:
    """M01 laser module serial driver."""

    def __init__(self, port='/dev/serial0', baud=9600, addr=0x00, timeout=1.0):
        import serial
        self._addr = addr
        self._ser = serial.Serial(port, baud, timeout=timeout)

    def measure_single(self):
        cmd = build_command_packet(FUNC_MEAS_SINGLE, addr=self._addr, data=[0x00])
        self._ser.write(cmd)
        self._ser.timeout = 4.0
        raw = self._ser.read(13)
        self._ser.timeout = 1.0
        return parse_response(raw)

    def close(self):
        self._ser.close()
