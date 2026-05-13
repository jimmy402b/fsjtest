# tests/test_m01.py
import pytest
from pi_collector.m01 import compute_checksum, bcd_to_distance, build_command_packet, parse_response

def test_compute_checksum():
    assert compute_checksum([0x00, 0x00, 0x20, 0x01, 0x00]) == 0x21

def test_compute_checksum_overflow():
    result = compute_checksum([0xFF, 0xFF, 0xFF])
    assert result == (0xFF + 0xFF + 0xFF) & 0xFF

def test_bcd_to_distance():
    assert bcd_to_distance(0x12345678) == 12345.678

def test_bcd_to_distance_zero():
    assert bcd_to_distance(0x00000000) == 0.0

def test_bcd_to_distance_max():
    assert bcd_to_distance(0x00000001) == 0.001

def test_build_write_command():
    cmd = build_command_packet(func_code=0x0020, addr=0x00, is_read=False, data=[0x00])
    assert cmd == bytes([0xAA, 0x00, 0x00, 0x20, 0x01, 0x00, 0x21])

def test_build_read_command():
    cmd = build_command_packet(func_code=0x0022, addr=0x00, is_read=True)
    assert cmd == bytes([0xAA, 0x80, 0x00, 0x22, 0x00, 0xA2])

def test_parse_response_valid():
    raw = bytes([0xAA, 0x00, 0x00, 0x20, 0x06, 0x12, 0x34, 0x56, 0x78, 0x04, 0xB0, 0xEE])
    distance, signal = parse_response(raw)
    assert distance == 12345.678
    assert signal == 0x04B0

def test_parse_response_bad_header():
    raw = bytes([0xBB, 0x00, 0x00, 0x20, 0x06, 0x12, 0x34, 0x56, 0x78, 0x04, 0xB0, 0x00])
    result = parse_response(raw)
    assert result is None

def test_parse_response_bad_checksum():
    raw = bytes([0xAA, 0x00, 0x00, 0x20, 0x06, 0x12, 0x34, 0x56, 0x78, 0x04, 0xB0, 0xFF])
    result = parse_response(raw)
    assert result is None

def test_parse_response_too_short():
    raw = bytes([0xAA, 0x00, 0x00])
    result = parse_response(raw)
    assert result is None
