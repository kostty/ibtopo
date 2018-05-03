#!/usr/bin/python

"""
Todo:
  * Add support for Intel's host naming style in ibnetdiscover, i.e.
    the hostname goes as the last word
  * Hide Switches= when empty and/or on demand (via argument)
  * Configurable switch names, e.g. switch, S, edge etc
  * Configurable levels of ISLs
"""

import os.path
import argparse
import subprocess
import re
import hostlist
import json
from fractions import Fraction

switches = {}
hosts = []

script_name = os.path.basename(__file__)
ibnetdiscover_cmd = '/usr/sbin/ibnetdiscover'
ibnetdiscover_args = ''

parser = argparse.ArgumentParser(description = '''`{}` parses `ibnetdiscover`
         output to generate a Slurm topology file and extract some other useful
         information'''.format(script_name))
parser.add_argument('-f', '--input-file',
                    help='A file containing an output of `ibnetdiscover`')
parser.add_argument('-d', '--dump', action='store_true',
                    help='Dump the internal structure in JSON')
parser.add_argument('-n', '--nodes-only', action='store_true',
                    help='Only list connected nodes, not switches')
parser.add_argument('-I', '--ibnetdiscover-path',
                    help='The full path to the `ibnetdiscover` program')
parser.add_argument('-A', '--ibnetdiscover-args',
                    help='''Additional arguments to be passed to the
          `ibnetdiscover` program (needs to be quoted, e.g. -A"--help"''')
parser.add_argument('-P', '--prefix', default = 'Switch',
                    help='Prefix to use when generating switch names')
args = parser.parse_args()
args = vars(args)

input_file = args['input_file']
prefix = args['prefix']
nodes_only = args['nodes_only']

if args['ibnetdiscover_path']:
    ibnetdiscover_cmd = args['ibnetdiscover_path']

if args['ibnetdiscover_args']:
    ibnetdiscover_args = args['ibnetdiscover_args']

if input_file:
    try:
        f = open(input_file, 'r')
    except IOError as e:
        print('Error: {}: "{}"'.format(e.strerror, input_file))
        exit(2)
else:
    cmd = [ ibnetdiscover_cmd ]
    cmd.append(ibnetdiscover_args)
    cmd_str = ' '.join(cmd)
    try:
        f = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        f = f.split('\n')
    except OSError as e:
        if e.errno == 2:
            print('Error: `{}` couldn\'t be found'.format(cmd_str))
            exit(3)
    except subprocess.CalledProcessError as e:
        print('`{}` exited with rc={}\n'.format(cmd_str, e.returncode))
        print('The error message was as follows:\n\n {}'.format(e.output))
        exit(4)

in_switch = False
for line in f:
    line = line.rstrip()
    if re.match('Switch.*', line):
        parts = line.split('"',4)
        guid, name = parts[1], parts[3]
        lid = re.search('.* lid (\d+) .*', parts[4]).group(1)
        ports = int(re.split('\s+', parts[0])[1])
        switches[guid] = {'name': name, 'lid': lid, 'ports': ports,
                          'hosts': {}, 'switches': {}}
        in_switch = guid
    elif re.match('\[.*', line):
        if not in_switch:
            continue
        switch = switches[in_switch]
        parts = line.split('"',4)
        guid = parts[1]
        name = parts[3]
        lid = re.search('.* lid (\d+) .*', parts[4]).group(1)
        remote_port = parts[2].strip(' #[]')
        if re.match('H-', guid):
            name = name.split(' ')
            hca, name = name[1], name[0]
            if guid in switch['hosts']:
                switch['hosts'][guid]['links'] += 1
            else:
                switch['hosts'][guid] = {'links': 1, 'lid': lid, 'name': name,
                                                                   'hca': hca}
        elif re.match('S-', guid):
            if guid in switch['switches']:
                switch['switches'][guid]['links'] += 1
            else:
                switch['switches'][guid] = {'links': 1}
    else:
        in_switch = False

if args['dump']:
    print json.dumps(switches, indent=4)
else:
    num2guid = {}
    output = [[], []]
    out_len = 0
    #prefix = 'Switch'
    for i, guid in enumerate(switches):
        num2guid[guid] = i+1
    for guid, info in switches.items():
        switch = '{}{}'.format(prefix, num2guid[guid])
        nodes = [ n['name'] for n in info['hosts'].values() ]
        n_links = sum([n['links'] for n in info['hosts'].values()])
        sw_links = sum([s['links'] for s in info['switches'].values()])
        nodes = hostlist.collect_hostlist(nodes)
        out_str = 'SwitchName={} Nodes={}'.format(switch, nodes)
        if not nodes_only:
            isl = [ '{}{}'.format(prefix,
                                       num2guid[x]) for x in info['switches']]
            isl = hostlist.collect_hostlist(isl)
            out_str += ' Switches={}'.format(isl)
        #print('ports: {}, isl: {}, nodes: {}'.format(info['ports'], sw_links, n_links))
        b_factor = Fraction(info['ports'] - sw_links, sw_links)
        comment = '# Free ports: {},'.format(info['ports'] -
                                                         (n_links + sw_links))
        comment += '\tblocking-factor: {}:{}'.format(b_factor.numerator,
                                                         b_factor.denominator)
	out_len = max(len(out_str), out_len)
	output[0].append(out_str)
	output[1].append(comment)
     
    output = ['{:<{}} {}'.format(out_str, out_len, comment) for out_str, comment in zip(output[0], output[1])]
    print('\n'.join(output))
