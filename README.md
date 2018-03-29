# ibtopo

usage: `ibtopology.py [-h] [-d] input_file`

ibtopology.py parses ibnetdiscover output to generate a Slurm topology file
and extract some other useful information

- positional arguments:

    input_file  A file containing the output of ibnetdiscover

- optional arguments:

    -h, --help  show this help message and exit
    -d, --dump  Dump the internal structure in JSON
