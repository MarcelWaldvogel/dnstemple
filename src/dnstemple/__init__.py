#!/usr/bin/python3
# Usage: dnstemple [-c dnstemple.yaml] <zonefile>…
# Sets variables (for {} substitution) and addresses (for `$ADDRESS`
# substitution) from the configuration file and processes zone files, including
# `$INCLUDE` support

import argparse
import ipaddress
import sys
import time
import uuid

import dns.exception
import dns.rdatatype
import dns.resolver
import yaml

# For Python<3.8 instead of importlib.metadata
from importlib_metadata import version, PackageNotFoundError

try:
    VERSION = version('fake_super')
except PackageNotFoundError:
    # package is not installed
    VERSION = '[UNKNOWN]'


def soa_serial_for_today():
    soa = time.strftime("%Y%m%d00", time.gmtime())
    return int(soa)


def soa_serial_for_now():
    return int(time.time())


def maybe_addr(addresses, domain, qtype):
    try:
        answer = dns.resolver.resolve(domain, qtype, search=False)
        addresses.append(answer[0].address)
    except dns.exception.DNSException:
        pass
    return addresses


def resolver_for(domain, mname):
    """Return a resolver object whose nameservers are obtained by
    asking the SOA MNAME (master name) for its addresses and listing
    the remaining NS addresses after that. Master is assumed to be
    most up-to-date, but may not always be reachable."""
    addresses = []
    maybe_addr(addresses, mname, 'AAAA')
    maybe_addr(addresses, mname, 'A')
    answer = dns.resolver.resolve(domain, 'NS', search=False)
    for ns in answer:
        maybe_addr(addresses, ns.target, 'AAAA')
        maybe_addr(addresses, ns.target, 'A')
    if len(addresses) == 0:
        exit("No NS addresses found for {domain}, {mname}")
    res = dns.resolver.Resolver(configure=False)
    res.nameservers = addresses
    return res


def get_serial(domain, mode):
    if mode is None or mode == 'unixtime':
        return soa_serial_for_now()
    elif mode == 'dateserial':
        return soa_serial_for_today()
    elif mode == 'online':
        soa = soa_serial_for_today() - 1
        try:
            answers = dns.resolver.resolve(domain, 'SOA', search=False)
            if answers[0].serial > soa:
                soa = answers[0].serial
            # Try to get from origin
            res = resolver_for(domain, answers[0].mname)
            answers = res.resolve(domain, 'SOA', search=False)
            if answers[0].serial > soa:
                soa = answers[0].serial
            return soa + 1  # Next
        except dns.exception.DNSException as e:
            sys.stderr.write(f"""WARNING: Could not obtain current SOA serial for {domain}
({e}), falling back to {soa + 1}\n""")
        return soa + 1
    else:
        # An integer constant?
        try:
            return int(mode)
        except ValueError:
            exit(f"Unknown value for config.serial: {mode}")


def expand_variables(filename, line, config):
    try:
        return line.format_map(config['variables'])
    except KeyError as k:
        exit(f"Unknown variable {k} in {filename}: {line}")


def expand_default(filename, line, config):
    (token, var, default) = line.split(maxsplit=2)
    if var not in config['variables'] or config['variables'][var] == '':
        config['variables'][var] = default
    return ''


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
        exit("Format mismatch `$ADDRESS <file> [<var>=<value>…]`"
             f" in {filename}: {line}")
    # Add arguments to copy of config variables (partial deep copy)
    config = dict(config)
    config['variables'] = dict(config['variables'])
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
            if not line.startswith(';'):
                line = expand_variables(filename, line, config)
            if line.startswith('$ADDRESS'):
                output += expand_address(filename, line, config)
                expect_name = True
            elif line.startswith('$INCLUDE'):
                output += expand_include(filename, line, config)
                expect_name = True
            elif line.startswith('$DEFAULT'):
                output += expand_default(filename, line, config)
                expect_name = True
            elif line.startswith('$'):
                output.append(line)
                expect_name = True
            elif line.startswith(';'):
                # Do not warn and keep expectations
                if 'comment' not in config['config']['skip']:
                    output.append(line)
            elif line == '':
                # Do not warn and keep expectations
                if 'empty' not in config['config']['skip']:
                    output.append(line)
            else:
                if expect_name and line[0] in ' \t':
                    sys.stderr.write("WARNING: Line may have undefined name"
                                     f" in {filename}: {line}\n")
                output.append(line)
                expect_name = False
    return output


def load_config(filename):
    with open(filename) as cfg:
        config = yaml.safe_load(cfg)
        config['variables']['_config'] = filename
        return config


def write_if_changed(filename, contents):
    # Ignore changes in the first line only (the SOA record)
    try:
        with open(filename, 'r') as file:
            old_contents = file.read()
    except FileNotFoundError:
        old_contents = None
    if old_contents != contents:
        with open(filename, 'w') as file:
            file.write(contents)
        return True
    else:
        return False


def process_files(config, args):
    if len(args) == 0:
        exit("No zone file provided")
    if ('extensions' not in config or 'in' not in config['extensions']
            or 'out' not in config['extensions']):
        exit("extensions.in and extensions.out required in config file")
    extin = config['extensions']['in']
    extout = config['extensions']['out']
    if extin == extout:
        exit("extensions.in and extensions.out need to differ")
    # Speed up tests for `config.skip`
    if 'config' not in config:
        config['config'] = {}
    if 'skip' not in config['config']:
        config['config']['skip'] = ''

    domains = set()
    mod_domains = set()
    for filename in args:
        # Remove extension, if possible
        if (filename.endswith(extin)):
            domain = filename[:-len(extin)]
        else:
            domain = filename
        domains.add(domain)
        # As these values will be overwritten every time,
        # they can share/reuse the same dict
        config['variables']['_domain'] = domain
        try:
            serial_mode = config['config']['serial']
        except KeyError:
            serial_mode = None
        config['variables']['_serial'] = get_serial(domain, serial_mode)
        if write_if_changed(domain + extout,
                            '\n'.join(process(filename, config)) + '\n'):
            mod_domains.add(domain)
    return (domains, mod_domains)


def update_catalog(config, domains):
    if 'domain' not in config['catalog']:
        exit("catalog requires catalog.domain")
    if 'catalog' not in config['extensions']:
        exit("catalog requires extensions.catalog")

    changed = False
    domain = config['catalog']['domain']
    ext = config['extensions']['catalog']
    fn = domain + ext
    # Read catalog
    lines = []
    ptrs = set()
    try:
        with open(fn, 'r') as f:
            for line in f.readlines():
                parts = line.strip().split()
                if len(parts) > 2 and parts[-2].upper() == 'PTR':
                    if parts[-1][:-1] in domains:
                        # In existing catalog, keep
                        lines.append(line)
                        ptrs.add(parts[-1][:-1])
                    else:
                        # In existing catalog, remove
                        changed = True
                else:
                    lines.append(line)
    except FileNotFoundError:
        # Use a default context with NS for backward compatibility
        lines = [
            f'@\t0\tSOA\tns.{domain}. hostmaster.{domain}. 1 1h 30m 1w 5m\n'
            f'\t0\tNS\tns.{domain}.\n'
            'version\t0\tTXT\t"2"\n'
        ]
        changed = True

    # Not yet in catalog, add
    for d in domains - ptrs:
        u = str(uuid.uuid4())
        lines.append(f'{u}.zones\t0\tPTR\t{d}.\n')
        changed = True

    if changed:
        with open(fn, 'w') as f:
            f.write(''.join(lines))
    return changed


def main(sysargv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="""Simple yet powerful DNS TEMPlating Engine""")
    parser.add_argument('--version',
                        action='version',
                        version=VERSION)
    parser.add_argument('--config', '-c',
                        default='dnstemple.yaml',
                        help="The configurion file to use")
    parser.add_argument('files',
                        nargs='+',
                        help="List of template files")
    args = parser.parse_args(sysargv)

    config = load_config('dnstemple.yaml')
    (domains, mod_domains) = process_files(config, args.files)
    if 'catalog' in config:
        if len(domains) > 1 or ('maintain' in config['catalog']
                                and config['catalog']['maintain'] == 'always'):
            if update_catalog(config, domains):
                print(config['catalog']['domain'])
    if len(mod_domains) > 0:
        print('\n'.join(mod_domains))


if __name__ == '__main__':
    main()
