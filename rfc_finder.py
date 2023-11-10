#  ______  _______ _______    _______ _           _             
# (_____ \(_______|_______)  (_______|_)         | |            
#  _____) )_____   _          _____   _ ____   __| |_____  ____ 
# |  __  /|  ___) | |        |  ___) | |  _ \ / _  | ___ |/ ___)
# | |  \ \| |     | |_____   | |     | | | | ( (_| | ____| |    
# |_|   |_|_|      \______)  |_|     |_|_| |_|\____|_____)_|    
#                                                               
#
# created with https://manytools.org/hacker-tools/ascii-banner/

"""
RFC Finder is a web application that is meant to be an IETF RFCs
information retrieval system to be used by researchers and implementers
of Internet Standards. It consists of a frontend written in HTML, CSS,
and JavaScript and a Python backend. This module is part of the backend
implementation of the RFC Finder web application.

This module makes use of bottle (https://bottlepy.org/docs/dev/) in
order to implement a web service that interacts with the front end
using a REST based API returning payloads in JSON format.

`http://127.0.0.1:5000/search` is the API endpoint where search terms
are received and used as a query to an inverted index built with all
the RFCs in ASCII format hosted in the RFC Editor web site
(https://www.rfc-editor.org/). The search is performed by a separate
module, `search`, also part of this project.

Docstrings in this module styled according to the `NumPy Style Guide
for Docstrings https://numpydoc.readthedocs.io/en/latest/format.html`_.
"""

__author__ = "Gilberto Ramirez"
__license__ = "MIT"
__version__ = "0.0.1"
__email__ = "ger6@illinois.edu"
__status__ = "Prototype"

from bottle import route, run, request, get
from bottle import hook, response, HTTPResponse, static_file
import rfcs

cors_headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    # 'Access-Control-Allow-Headers': 'X-Token, ...',
    # 'Access-Control-Expose-Headers': 'X-My-Custom-Header, ...',
    # 'Access-Control-Max-Age': '86400',
    # 'Access-Control-Allow-Credentials': 'true',
}

print("""
 ______  _______ _______    _______ _           _             
(_____ \(_______|_______)  (_______|_)         | |            
 _____) )_____   _          _____   _ ____   __| |_____  ____ 
|  __  /|  ___) | |        |  ___) | |  _ \ / _  | ___ |/ ___)
| |  \ \| |     | |_____   | |     | | | | ( (_| | ____| |    
|_|   |_|_|      \______)  |_|     |_|_| |_|\____|_____)_|    

v 0.0.1 | MIT License | 2023 | by Gilberto Ramirez <ger6@illinois.edu>
""")

@hook('before_request')
def handle_options():
    if request.method == 'OPTIONS':
        # Bypass request routing and immediately return a response
        raise HTTPResponse(headers=cors_headers)

@hook('after_request')
def enable_cors():
    for key, value in cors_headers.items():
       response.set_header(key, value)

@route('/')
def healthcheck():
  return "All good with root!"

@route('/search')
def search_terms():
  global rfcs_corpus

  q = request.query.q
  return rfcs_corpus.search(q)

@route('/topics')
def search_terms():
  global rfcs_corpus

  docid = request.query.docid
  return rfcs_corpus.get_topics(docid)

@route('/favicon.ico')
def get_favicon():
  return static_file('icon-16.png', root='./images/')

rfcs_corpus = rfcs.RFCs()

run(host='localhost', port=5000, debug=True)
