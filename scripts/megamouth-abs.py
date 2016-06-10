#!/usr/bin/env python

"""
run processes to create Nature full corpus
"""

from baleen.pipeline import script
from baleen.steps import *

from megamouth.steps import get_abs

script(steps=[get_abs,
              core_nlp,
              lemma_trees,
              ext_vars,
              offsets,
              prep_vars,
              prune_vars,
              tocsv,
              setup_server,
              toneo,
              ppgraph,
              add_cit],
       optional=[remove_server,
                 start_server,
                 stop_server, clean],
       default_cfg_fnames=['megamouth.ini', 'local.ini'],
       default_section='ABS')
