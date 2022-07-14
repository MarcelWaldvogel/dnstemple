from pytest import raises
import re
import dnstemple

# In the real code, `variables` will always be defined;
# in the tests, it has to be done manually, however.


def test_expand_ipv4():
    assert dnstemple.expand_address(
        "a.zone", '$ADDRESS\tx\t@',
        {
            'addresses': {'x': "1.2.3.4"},
            'variables': {}
        }
    ) == ["@\t\tA\t1.2.3.4"]


def test_expand_ipv4_ipv6():
    assert dnstemple.expand_address(
        "a.zone", '$ADDRESS\tx\t@',
        {
            'addresses': {'x': "1.2.3.4 ::1"},
            'variables': {}
        }
    ) == ["@\t\tA\t1.2.3.4", "@\t\tAAAA\t::1"]


def test_expand_variable():
    assert dnstemple.expand_address(
        "a.zone", '$ADDRESS\tx\t@',
        {
            'addresses': {'x': "{y}"},
            "variables": {'y': "1.2.3.4 ::1"}
        }
    ) == ["@\t\tA\t1.2.3.4", "@\t\tAAAA\t::1"]


def test_expand_variable_plus():
    assert dnstemple.expand_address(
        "a.zone", '$ADDRESS\tx\t@',
        {
            'addresses': {'x': "{y} 127.0.0.1 {y}"},
            "variables": {'y': "1.2.3.4 ::1"}
        }
    ) == [
        "@\t\tA\t1.2.3.4",
        "@\t\tAAAA\t::1",
        "@\t\tA\t127.0.0.1",
        "@\t\tA\t1.2.3.4",
        "@\t\tAAAA\t::1"
    ]


def test_expand_recursive():
    assert dnstemple.expand_address(
        "a.zone", '$ADDRESS\tx\t@',
        {
            'addresses': {
                'x': "y z",
                'y': "1.2.3.4",
                "z": "127.0.0.1 ::1"
            },
            "variables": {}
        }
    ) == [
        "@\t\tA\t1.2.3.4",
        "@\t\tA\t127.0.0.1",
        "@\t\tAAAA\t::1"
    ]


def test_expand_too_deep():
    with raises(RecursionError, match=r'Address expansion too deep'):
        dnstemple.expand_address(
            "a.zone", '$ADDRESS\tx\t@',
            {
                'addresses': {
                    'x': "x y z",
                    'y': "1.2.3.4",
                    "z": "127.0.0.1 ::1"
                },
                "variables": {}
            }
        )


def test_expand_invalid():
    with raises(ValueError,
                match=re.escape(r'Address "fails" unknown expanding "z"'
                                ' (expanded from address "y"'
                                ' (expanded from address "x"))')):
        dnstemple.expand_address(
            "a.zone", '$ADDRESS\tx\t@',
            {
                'addresses': {
                    'x': "y",
                    'y': "z",
                    "z": "fails"
                },
                "variables": {}
            }
        )
