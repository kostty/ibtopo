# ibtopology

usage: `ibtopology [-h] [-f PATH] [-d] [-n] [-I PATH] [-A ARGS] [-P PREFIX]
                  [-O]`

`ibtopology` parses `ibnetdiscover` output to generate a Slurm topology file
and extract some other useful information

* optional arguments:

  `-h`, `--help`            show this help message and exit
  
  `-f PATH`, `--input-file PATH`
                        A file containing the output of `ibnetdiscover`
                        
  `-d`, `--dump`            Dump the internal structure in JSON
  
  `-n`, `--nodes-only`      Only list connected nodes, not switches
  
  `-I PATH`, `--ibnetdiscover-path PATH`
                        The full path to the `ibnetdiscover` program
                        
  `-A ARGS`, `--ibnetdiscover-args ARGS`
                        Additional arguments to be passed to the
                        `ibnetdiscover` program (needs to be quoted, e.g. `-A"
                        --help"`
                        
  `-P PREFIX`, `--prefix PREFIX`
                        Prefix to use when generating switch names
                        
  `-O`, `--omni-path`       The fabric is based on Intel's Omni-Path
