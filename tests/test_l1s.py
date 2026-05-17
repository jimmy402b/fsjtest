import pytest
from pi_collector.l1s import parse_response


def test_parse_success():
    dist, sig = parse_response('D=1.314m,520#\r\n')
    assert dist == 1.314
    assert sig == 520


def test_parse_success_zero_distance():
    dist, sig = parse_response('D=0.000m,100#')
    assert dist == 0.0
    assert sig == 100


def test_parse_success_long_distance():
    dist, sig = parse_response('D=40.000m,999#')
    assert dist == 40.0
    assert sig == 999


def test_parse_error():
    result = parse_response('E=258\r\n')
    assert result == (None, 258)


def test_parse_error_weak_reflection():
    result = parse_response('E=255')
    assert result == (None, 255)


def test_parse_empty():
    assert parse_response('') is None


def test_parse_garbage():
    assert parse_response('\x00\xff\x00') is None


def test_parse_whitespace_only():
    assert parse_response('   \r\n  ') is None


def test_parse_malformed_d():
    assert parse_response('D=abc,123#') is None
