#!/usr/bin/python3
# Usage: dnstemple [-c dnstemple.yaml] <zonefile>…
# Sets variables (for {} substitution) and addresses (for `$ADDRESS`
# substitution) from the configuration file and processes zone files, including
# `$INCLUDE` support

import ipaddress
import sys

#import dns
import yaml

def expand_variables(filename, line, config):
    try:
        return line.format_map(config['variables'])
    except KeyError as k:
        exit(f"Unknown variable {k} in {filename}: {line}")


def expand_address(filename, line, config):
    (token, addr, prefix) = line.split(maxsplit=2)
    # KeyError caught in caller
    addresses = config['addresses'][addr]
    output = []
    for a in addresses.split():
        ipa = ipaddress.ip_address(a)
        if isinstance(ipa, ipaddress.IPv4Address):
            output.append(f'{prefix}\tA\t{a}')
        else:
            output.append(f'{prefix}\tAAAA\t{a}')
    return output


def expand_include(filename, line, config):
    args = line.split()
    if len(args) < 2:
        exit(f"Format mismatch `$ADDRESS <file> [<var>=<value>…]` in {filename}: {line}")
    # Add arguments to copy of config
    config = dict(config)
    for arg in args[2:]:
        (key, value) = arg.split('=')
        config['variables'][key] = value
    # Recurse into include file
    return process(args[1], config)


def process(filename, config):
    output = []
    with open(filename, 'r') as f:
        for line in f.readlines():
            line = line.strip()
            line = expand_variables(filename, line, config)
            if line.startswith('$ADDRESS'):
                output += expand_address(filename, line, config)
            elif line.startswith('$INCLUDE'):
                output += expand_include(filename, line, config)
            else:
                output.append(line)
    return output


def load_config(filename):
    with open(filename) as cfg:
        return yaml.safe_load(cfg)


def main(args):
    if len(args) > 1 and args[0] == '-c':
        config = load_config(args[1])
        args = args[2:]
    else:
        config = load_config('dnstemple.yaml')
    if len(args) == 0:
        exit("No zone file provided")
    for filename in args:
        print('\n'.join(process(filename, config)))


if __name__ == '__main__':
    main(sys.argv[1:])
