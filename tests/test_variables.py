from pytest import raises
import dnstemple


def test_expand_none():
    assert dnstemple.expand_variables(
        'a.zone', '@\tTXT\t"test"', {'variables': {}}) == '@\tTXT\t"test"'


def test_expand_one():
    assert dnstemple.expand_variables(
        'a.zone', '{one}\tTXT\t"test"',
        {'variables': {'one': 'eins'}}) == 'eins\tTXT\t"test"'


def test_expand_two():
    assert dnstemple.expand_variables(
        'a.zone', '{one}\tTXT\t"{two}"',
        {'variables': {'one': 'eins', 'two': 'zwei'}}) == 'eins\tTXT\t"zwei"'


def test_expand_bad():
    with raises(SystemExit, match=r'Unknown variable'):
        dnstemple.expand_variables(
            'a.zone', '{one}\tTXT\t"{three}"',
            {'variables': {'one': 'eins', 'two': 'zwei'}})
