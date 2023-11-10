#     _ _                                  
#    | (_)                                 
#  __| |_  ___  ____ ___ _   _ _____  ____ 
# / _  | |/___)/ ___) _ \ | | | ___ |/ ___)
#( (_| | |___ ( (__| |_| \ V /| ____| |    
# \____|_(___/ \____)___/ \_/ |_____)_|    
#                                          
#                  _                       
#   _             (_)                      
# _| |_ ___  ____  _  ____  ___            
#(_   _) _ \|  _ \| |/ ___)/___)           
#  | || |_| | |_| | ( (___|___ |           
#   \__)___/|  __/|_|\____|___/            
#           |_|                            
#
# created with https://manytools.org/hacker-tools/ascii-banner/

"""
This module, `discover_topics`, is only called from the command line and
performs unsupervised discovery of topics using LDA with Gibbs sampling
on the RFCs corpus. This can be run once the corpus has been downloaded
and prepared for MeTA (https://meta-toolkit.org/) ingestion using the
`get_rfcs` program.

Process can take a long time depending on the number of topics (k)
given ranging from 20 minutes to more than one hour on an Apple M1 Pro
with 32 GB of RAM, so please be patient. Once the discovery process
concludes, results will be saved inside files with names such as
`lda-pgibbs-#` where # is the number of topics (k) given. It is
recommended you run this every time the corpus is updated, so the
topics functionality of RFC Finder can become available.

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
import time
from datetime import datetime
from pathlib import Path

def main():
  parser = argparse.ArgumentParser(
    description='Discover topics using LDA (unsupervised) Gibbs sampling.'
  )
  parser.add_argument('k', type=int, nargs='?', default=20,
                      help='number of topics to discover')
  parser.add_argument('alpha', type=float, nargs='?', default=0.1,
                      help='Gibbs sampling alpha parameter')
  parser.add_argument('beta', type=float, nargs='?', default=0.1,
                      help='Gibbs sampling beta parameter')
  parser.add_argument('iters', type=int, nargs='?', default=1000,
                      help='number of iterations in Gibbs sampling')
  args = parser.parse_args()

  print("""
     _ _                                  
    | (_)                                 
  __| |_  ___  ____ ___ _   _ _____  ____ 
 / _  | |/___)/ ___) _ \ | | | ___ |/ ___)
( (_| | |___ ( (__| |_| \ V /| ____| |    
 \____|_(___/ \____)___/ \_/ |_____)_|    
                                          
                  _                       
   _             (_)                      
 _| |_ ___  ____  _  ____  ___            
(_   _) _ \|  _ \| |/ ___)/___)           
  | || |_| | |_| | ( (___|___ |           
   \__)___/|  __/|_|\____|___/            
           |_|                            

v 0.0.1 | MIT License | 2023 | by Gilberto Ramirez <ger6@illinois.edu>
  """)

  fidx = metapy.index.make_forward_index('config.toml')
  dset = metapy.learn.Dataset(fidx)

  print("[" + str(datetime.now()) + "] Running discovery of " +
        str(args.k) + " topics using LDA Gibbs sampling with " +
        "alpha = " + str(args.alpha) + ", beta = " + str(args.beta) +
        ", iters = " + str(args.iters))
  print("[" + str(datetime.now()) + "] Please be patient. As an example, " +
        "discovering 20 topics might take 20 to 30 minutes in a 2021 MacBook Pro...")

  start_time = time.time()

   # create 'models/' path if it does not exist
  Path("models/").mkdir(parents=True, exist_ok=True)
  filename = 'models/lda-pgibbs-{}'.format(args.k)

  # now the heavy lifting... run LDA parallel Gibbs on corpus  
  model = metapy.topics.LDAParallelGibbs(docs=dset, num_topics=args.k, alpha=0.1, beta=0.1)
  model.run(num_iters=args.iters)
  model.save(filename)

  elapsed_time = int((time.time() - start_time) / 60)  # elapsed time in minutes

  print("[" + str(datetime.now()) + "] All done! Results were written to '" +
        filename + "'. Now you are ready to explore topics in RFC Finder!")
  print("[" + str(datetime.now()) + "] It took me " + str(elapsed_time) +
        " minutes to discover " + str(args.k) + " topics")
  print("[" + str(datetime.now()) + "] Bye!")

if __name__ == "__main__":
  main()