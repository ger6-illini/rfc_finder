#                     d8P           
#                  d888888P         
#  d888b8b   d8888b  ?88'           
# d8P' ?88  d8b_,dP  88P            
# 88b  ,88b 88b      88b            
# `?88P'`88b`?888P'  `?8b           
#        )88                        
#       ,88P                        
#   `?8888P                         
#             ,d8888b               
#             88P'                  
#          d888888P                 
#   88bd88b  ?88'     d8888b .d888b,
#   88P'  `  88P     d8P' `P ?8b,   
#  d88      d88      88b       `?8b 
# d88'     d88'      `?888P'`?888P' 
#
# created with https://manytools.org/hacker-tools/ascii-banner/

"""
This module, `get_rfcs`, is only called from the command line and
maintains a local copy of the entire RFCs corpus using the `rsync`
service provided by the RFC Editor web site
(https://www.rfc-editor.org/)`. When run for the first time, `get_rfcs`
will take some time and will download the more than 10,000 documents
in the RFCs corpus.

Once the entire corpus is downloaded, subsequent calls to `get_rfcs`
will just download those files that have been added or changed avoiding
unnecessary transfers of unchanged files.

`get_rfcs` also create/update the file
`rfc-finder/corpus/rfcs-full-corpus.txt` which lists all the files in
the corpus in a format that makes it usable by the `metapy toolkit`
(https://github.com/meta-toolkit/metapy).

Docstrings in this module styled according to the `NumPy Style Guide
for Docstrings https://numpydoc.readthedocs.io/en/latest/format.html`_.
"""

__author__ = "Gilberto Ramirez"
__license__ = "MIT"
__version__ = "0.0.1"
__email__ = "ger6@illinois.edu"
__status__ = "Prototype"

import argparse
import metapy
import os
import pytoml
import re
import subprocess
import sys
import time

def main():
  parser = argparse.ArgumentParser(
    description='Create/maintains a local copy of the RFCs corpus.'
  )
  args = parser.parse_args()
  print("""
                     d8P           
                  d888888P         
  d888b8b   d8888b  ?88'           
 d8P' ?88  d8b_,dP  88P            
 88b  ,88b 88b      88b            
 `?88P'`88b`?888P'  `?8b           
        )88                        
       ,88P                        
   `?8888P                         
             ,d8888b               
             88P'                  
          d888888P                 
   88bd88b  ?88'     d8888b .d888b,
   88P'  `  88P     d8P' `P ?8b,   
  d88      d88      88b       `?8b 
 d88'     d88'      `?888P'`?888P' 

v 0.0.1 | MIT License | 2023 | by Gilberto Ramirez <ger6@illinois.edu>
  """)

  start_time = time.time()

  if not os.path.isdir('corpus/'):
    sys.exit('Error: `corpus/` folder does not exist.')
  print("`corpus/` folder exists... good!")

  if not os.path.isfile('corpus/file.toml'):
    sys.exit('Error: `corpus/file.tml` file does not exist.')
  print("`corpus/file.toml` file exists... good!")

  # `rsync` allows to get a local copy of the entire corpus of RFCs
  # making use of the free `rsync` service hosted by the RFC Editor
  # (see https://www.rfc-editor.org/retrieve/rsync/). This service
  # allows to transfer just those files that have changed, so the
  # first time is run it might take time (less than 5 minutes on a
  # decent Internet connection) and rest of times will last no more
  # than few seconds
  if not os.path.isdir('corpus/rfcs/'):
    print("`rsync` will run for the first time. Please be patient...")
  result = subprocess.run(['rsync', '-aivz', '--delete',
    'rsync.rfc-editor.org::rfcs-text-only', 'corpus/rfcs/'],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
  if result.returncode != 0:
    sys.exit(result.stderr)
  # get number of files added/modified/deleted by rsync
  file_count = result.stdout.count('\n') - 4
  print("`rsync` completed... {} files added/modified/deleted.".format(file_count))

  # update `corpus/rfcs-full-corpus.txt` if one or more files have changed
  # also recreate the inverted index
  if file_count > 0:

    # get a list of all files in `path` with names of the form 'rfc'`number`'.txt'
    # where `number` is an integer with no leading zeroes identifying the RFC number
    corpus_filenames = [corpus_filename for corpus_filename in os.listdir('corpus/rfcs/')
                        if re.search(r'^rfc\d+\.txt$', corpus_filename)]
    corpus_filenames.sort()
    # parse content of 'file.toml' into `config`
    with open('corpus/file.toml', 'rb') as f:
        config = pytoml.load(f)
    # we will use value of 'list' key from `config` as part
    # of the file name containing all docs in corpus
    # see https://meta-toolkit.org/overview-tutorial.html
    filename = "corpus/%s-full-corpus.txt" % config['list']
    with open(filename, 'w') as f:
        for corpus_filename in corpus_filenames:
            f.write("[none] rfcs/{}\n".format(corpus_filename))
    print("file `{}` created!".format(filename))

    print("Recreating inverse index. Please be patient...")
    # delete existing inverted index
    result = subprocess.run(['rm', '-rf', 'idx/'],
      stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if result.returncode != 0:
      sys.exit(result.stderr)
    # create from scratch inverted index
    idx = metapy.index.make_inverted_index('config.toml')
    print("Inverse index done! {0} docs, {1} unique terms, avg doc length {2:.0f} chars."
          .format(idx.num_docs(), idx.unique_terms(), idx.avg_doc_length()))
    # create from scratch forward index
    fidx = metapy.index.make_forward_index('config.toml')
    print("Forward index done! {0} docs, {1} unique terms."
          .format(fidx.num_docs(), fidx.unique_terms()))

  elapsed_time = round(time.time() - start_time)
  print("Corpus update done! It took me {} seconds. Am I amazing or what?".format(elapsed_time))

if __name__ == "__main__":
  main()
