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

switches = {}
hosts = []

script_name = os.path.basename(__file__)
ibnetdiscover_cmd = '/usr/sbin/ibnetdiscover'
ibnetdiscover_args = ''

parser = argparse.ArgumentParser(description = '''{} parses ibnetdiscover
         output to generate a Slurm topology file and extract some other useful
         information'''.format(script_name))
parser.add_argument('-f', '--input-file',
                    help='A file containing an output of ibnetdiscover')
parser.add_argument('-d', '--dump', action='store_true',
                    help='Dump the internal structure in JSON')
parser.add_argument('-I', '--ibnetdiscover-path',
                    help='The full path to the `ibnetdiscover` program')
parser.add_argument('-A', '--ibnetdiscover-args',
                    help='''Additional arguments to be passed to the
                                             `ibnetdiscover` program''')

args = parser.parse_args()
args = vars(args)

input_file = args['input_file']

if args['ibnetdiscover_path']:
    ibnetdiscover_cmd = args['ibnetdiscover_path']

if input_file:
    try:
        f = open(input_file, 'r')
    except IOError as e:
        print('Error: {}: "{}"'.format(e.strerror, input_file))
        exit(2)
else:
    try:
        f = subprocess.check_output(ibnetdiscover_cmd, stderr=subprocess.STDOUT)
        f = f.split('\n')
    except OSError as e:
        if e.errno == 2:
            print('Error: {} couldn\'t be found'.format(ibnetdiscover_cmd))
            exit(3)
    except subprocess.CalledProcessError as e:
        print(e.args)
        print('{} returned the following error:\n\n{}'.format(e.cmd, e.output))
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
                          'hosts': [], 'switches': []}
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
            host = {'giud': guid, 'lid': lid, 'name': name, 'hca': hca}
            switch['hosts'].append(host)
        elif re.match('S-', guid):
            switch['switches'].append(guid)
    else:
        in_switch = False

if args['dump']:
    print json.dumps(switches, indent=4)
else:
    num2guid = {}
    prefix = 'Switch'
    for i, guid in enumerate(switches):
        num2guid[guid] = i+1
    for guid, info in switches.items():
        switch = '{}{}'.format(prefix, num2guid[guid])
        nodes = [ x['name'] for x in info['hosts'] ]
        num_nodes = len(nodes)
        nodes = hostlist.collect_hostlist(nodes)
        isl = [ '{}{}'.format(prefix, num2guid[x]) for x in info['switches']]
        isl = hostlist.collect_hostlist(isl)
        print('SwitchName={} Nodes={} Switches={}    # Free ports: {}'
               .format(switch, nodes, isl, info['ports'] - num_nodes))
