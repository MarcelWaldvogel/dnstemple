from mock import patch, mock_open


@patch('builtins.open', new_callable=mock_open, read_data='../some/path')
def test_config(mock_file):
    pass
