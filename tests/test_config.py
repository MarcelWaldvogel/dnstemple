from mock import patch, call, mock_open

import dnstemple


@patch('builtins.open', new_callable=mock_open, read_data='../some/path')
def test_config(mock_file):
    pass
