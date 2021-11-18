from mock import patch

import dnstemple


@patch('dnstemple.time.gmtime')
def test_today(mock_gmtime):
    mock_gmtime.return_value = (2021, 11, 18, 11, 21, 17, 4, 322, False)
    assert dnstemple.soa_serial_for_today() == 2021111800


@patch('dnstemple.time.time')
def test_now(mock_time):
    mock_time.return_value = 1637231137
    assert dnstemple.soa_serial_for_now() == 1637231137
