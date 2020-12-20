#!/usr/bin/python3
# Usage: dnstemple [-c dnstemple.yaml] <zonefile>…
# Sets variables (for {} substitution) and addresses (for `$ADDRESS`
# substitution) from the configuration file and processes zone files, including
# `$INCLUDE` support

import ipaddress
import sys
import time

import dns.resolver
import dns.rdatatype
import dns.exception
import yaml


def soa_serial_for_today():
    soa = time.strftime("%Y%m%d00", time.gmtime())
    return int(soa)


def get_serial(domain):
    soa = soa_serial_for_today()
    try:
        answers = dns.resolver.resolve(domain, dns.rdatatype.SOA,
                raise_on_no_answer=False, search=False)
        if answers[0].serial > soa:
            soa = answers[0].serial
            # Try to get from origin
            # XXX TODO
            return soa+1 # Next
    except dns.exception.DNSException as e:
        print(f"WARNING: Could not obtain current SOA serial ({e}), falling back to {soa}")
        return soa


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
        doubletab = '\t' if len(prefix) < 8 else ''
        if isinstance(ipa, ipaddress.IPv4Address):
            output.append(f'{prefix}{doubletab}\tA\t{a}')
        else:
            output.append(f'{prefix}{doubletab}\tAAAA\t{a}')
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
    expect_name = True
    with open(filename, 'r') as f:
        for line in f.readlines():
            line = line.rstrip()
            line = expand_variables(filename, line, config)
            if line.startswith('$ADDRESS'):
                output += expand_address(filename, line, config)
                expect_name = True
            elif line.startswith('$INCLUDE'):
                output += expand_include(filename, line, config)
                expect_name = True
            elif line.startswith('$'):
                output.append(line)
                expect_name = True
            elif line == '':
                # Do not warn and keep expectations
                output.append(line)
            else:
                if expect_name and line[0] in ' \t':
                    print(f"WARNING: Line may have undefined name in {filename}: {line}")
                output.append(line)
                expect_name = False
    return output


def load_config(filename):
    with open(filename) as cfg:
        config = yaml.safe_load(cfg)
        config['variables']['_config'] = filename
        return config


def main(args):
    if len(args) > 1 and args[0] == '-c':
        config = load_config(args[1])
        args = args[2:]
    else:
        config = load_config('dnstemple.yaml')
    if len(args) == 0:
        exit("No zone file provided")
    if ('extensions' not in config or 'in' not in config['extensions']
            or 'out' not in config['extensions']):
        exit("extensions.in and extensions.out required in config file")
    extin = config['extensions']['in']
    extout = config['extensions']['out']
    if extin == extout:
        exit("extensions.in and extensions.out need to differ")
    for filename in args:
        # Remove extension, if possible
        if (filename.endswith(extin)):
            domain = filename[:-len(extin)]
        else:
            domain = filename
        # As these values will be overwritten every time,
        # they can share/reuse the same dict
        config['variables']['_domain'] = domain
        config['variables']['_serial'] = get_serial(domain)
        with open(domain + extout, 'w') as file:
            file.write('\n'.join(process(filename, config)) + '\n')


if __name__ == '__main__':
    main(sys.argv[1:])
