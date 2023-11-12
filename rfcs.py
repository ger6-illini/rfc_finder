#  ______  _______ _______      
# (_____ \(_______|_______)     
#  _____) )_____   _        ___ 
# |  __  /|  ___) | |      /___)
# | |  \ \| |     | |_____|___ |
# |_|   |_|_|      \______|___/ 
#
#
# created with https://manytools.org/hacker-tools/ascii-banner/

"""
RFCs corpus data and metadata as fetched from the RFC Editor web site
(https://www.rfc-editor.org/).

Attributes
----------
metadata: dict
  Metadata fetched from the RFC Editor web site.

pi_df: pandas dataframe
  Dataframe containing topic coverage values per document per topic,
  i.e., the pi values. Every row is a document indexed by a document ID
  and every column corresponds to a column. Values are floats which
  represent probabilities of a given document to be part of a given
  topic. All probabilities across same row must add up to 1, i.e., a
  document cannot be part of other non-listed topics.

This class assumes all the IETF RFC files and all the configuration
files, i.e., `file.toml` and `rfcs-full-corpus.txt` are available in
the `./corpus/` folder. Please refer to
`https://github.com/ger6-illini/cs410-tis-fa23-final-project` for
more details on how to setup the RFC Finder applicatio before using
this class.

Docstrings in this module styled according to the `NumPy Style Guide
for Docstrings https://numpydoc.readthedocs.io/en/latest/format.html`_.
"""

__author__ = 'Gilberto Ramirez'
__license__ = 'MIT'
__version__ = '0.0.1'
__email__ = 'ger6@illinois.edu'
__status__ = 'Prototype'

import metapy
import numpy as np
import pandas as pd
import re
import xmltodict
from collections import OrderedDict

class RFCs:
  def __init__(self, filename='./corpus/rfcs/rfc-index.xml'):
    """
    Constructor loads the RFCs metadata which will be used to provide
    details on RFCs returned by the `search()` method or the `topics()`
    methods. It will also load the topics coverage matrix needed by
    the `topics()` method.

    Parameters
    ----------
    filename : str
      Absolute or relative path of the XML filename containing RFCs
      metadata. Default: './corpus/rfcs/rfc-index.xml'.

    Returns
    -------
    RFCs
      An instance of the RFCs class.
    """
    self.metadata = self.load_metadata(filename=filename)
    self.pi_df = self.load_topics_coverage()

  def load_metadata(self, filename):
    """
    Load RFCs metadata from `filename` (`./corpus/rfcs/rfc-index.xml` by
    default), a file maintained and provided by the RFC Editor web site
    (https://www.rfc-editor.org/), into the `metadata` property class.
    Another dict to map `doc-id`, e.g., RFC0001, to its corresponding
    index in the `rfc-index > rfc-entry` XML tree is built and added to
    the global dict (under the name `docid_to_index` to make metadata
    retrieval easier.

    Parameters
    ----------
    filename : str
      Absolute or relative path of the XML filename containing RFCs
      metadata. Default: './corpus/rfcs/rfc-index.xml'.

    Returns
    -------
    dict
      Dictionary with RFCs metadata.
    """

    metadata = {}

    with open(filename, encoding='utf8') as f:
      metadata = dict(xmltodict.parse(f.read()))

    # create `doc-id` to index dictionary to speed up metadata lookup
    metadata['docid_to_index'] = {}
    for i, rfc_entry in enumerate(metadata['rfc-index']['rfc-entry']):
      metadata['docid_to_index'][rfc_entry['doc-id']] = i

    return metadata

  def get_metadata(self, docid):
    """
    Get RFC metadata from `self.metadata`, the global dict loaded using
    the `load_rfcs_metadata()` function given a `docid`, e.g., RFC0001.

    Parameters
    ----------
    docid : str
      Document ID identifying the RFC such as RFC0001. It consists of
      the text 'RFC' followed by a four digit number including leading
      zeroes if any.

    Returns
    -------
    dict
      Dictionary containing the metadata for the RFC specified by `filename`.
    """

    # if `docid` does not exist in metadata return an empty dictionary 
    if docid not in self.metadata['docid_to_index'].keys():
      return {}

    # fetch/transform the selected metadata to return
    i = self.metadata['docid_to_index'][docid]
    title = self.metadata['rfc-index']['rfc-entry'][i]['title']
    if (type(self.metadata['rfc-index']['rfc-entry'][i]['author']) is not list):
      # only one author
      author_list = [self.metadata['rfc-index']['rfc-entry'][i]['author']['name']]
    else:
      # more than one author
      author_list = [author['name'] for author in
                    self.metadata['rfc-index']['rfc-entry'][i]['author']]
    authors = ', '.join(author_list)
    year = self.metadata['rfc-index']['rfc-entry'][i]['date']['year']
    pages = self.metadata['rfc-index']['rfc-entry'][i]['page-count']
    status = self.metadata['rfc-index']['rfc-entry'][i]['current-status']
    area = self.metadata['rfc-index']['rfc-entry'][i].get('area', '')
    wg = self.metadata['rfc-index']['rfc-entry'][i].get('wg_acronym', '')
    stream = self.metadata['rfc-index']['rfc-entry'][i].get('stream', '')
    abstract = ''
    if 'abstract' in self.metadata['rfc-index']['rfc-entry'][i].keys():
      abstract = self.metadata['rfc-index']['rfc-entry'][i]['abstract']['p']
      if type(abstract) is list:
        # needed in case abstract has more than one paragraph
        abstract = (' ').join(abstract)
    url = 'https://www.rfc-editor.org/rfc/rfc'
    url += str(int(re.search(r'\d+', docid).group())) + '.html'

    result = {
      'doc-id': docid,
      'title': title,
      'authors': authors,
      'year': year,
      'pages': pages,
      'status': status,
      'area': area,
      'wg' : wg,
      'stream' : stream,
      'abstract': abstract,
      'url': url,
    }

    return result

  def search(self, query_terms):
    """
    Implements a search across the entire RFCs corpus of a given query
    string, `query_terms`, using an inverted index and a BM25 ranker
    function. All the information retrieval calls use the `metapy
    toolkit` (https://github.com/meta-toolkit/metapy).

    Parameters
    ----------
    query_terms : str
      Query terms that need to be searched in the inverted index.

    Returns
    -------
    dict
      Dictionary with all results in the form of an array of dictionaries
      where each dictionary entry corresponds to RFC metadata of a
      relevant document returned by a ranker function running on top of
      an inverted index built for the RFCs corpus.
    """

    # settings to be used by BM25 ranker function
    settings = {
      'top_k': 10,
      'bm25_k1': 1.2,
      'bm25_b': 0.785,
      'bm25_k3': 500,
    }

    idx = metapy.index.make_inverted_index('config.toml')

    ranker = metapy.index.OkapiBM25(k1=settings['bm25_k1'],
                                    b=settings['bm25_b'],
                                    k3=settings['bm25_k3'])

    query = metapy.index.Document()
    query.content(query_terms)

    top_docs = []
    top_docs = ranker.score(idx, query, num_results=settings['top_k'])
    # `top_docs` is an array of tuples (`doc_idx`, `score`) sorted
    # by score in descending order. Example:
    #   [(0, 24.28896713256836),
    #    (13, 23.797449111938477),
    #    (8042, 16.87704849243164)]
    # `doc_idx` is the index internally assigned by the inverted index
    # used for information retrieval 

    results = []
    # fetch metadata for every relevant document returned by ranker
    p = re.compile(r'rfc(\d+).txt$')
    for (doc_idx, score) in top_docs:
      rfc_filename = idx.metadata(doc_idx).get('path')
      # transform `filename` into `docid`
      docid = 'RFC' + p.search(rfc_filename).group(1).zfill(4)
      result = self.get_metadata(docid)
      result['score'] = score
      results.append(result)
    # it seems returning a JSON array instead of a dictionary might might
    # be secure (https://haacked.com/archive/2009/06/25/json-hijacking.aspx/)
    results = {'results': results}

    return results

  def load_topics_coverage(self, num_topics=20):
    """
    Load the pi values (topic probabilities) for all documents in the
    RFCs corpus. It assumes the results of running an LDA model on the
    entire RFCs corpus are available in a file `models/lda-pgbibbs-#`
    where # is the number of topics given an input to the model. This is
    done since the process of discovering topics might take a long time
    (20, 30, 60, or more minutes depending on number of topics) and
    doing it ad-hoc will be unacceptable by the user. The program
    `discover_topics.py` can be run in case a specific model needs to be
    built for the first time or updates, e.g., when corpus changes or a
    new number of topics wants to be used.
    
    Parameters
    ----------
    num_topics : int
      Number of topics to be used in topic analysis. It will be used as
      part of the filename storing model parameters. Default: 20.

    Returns
    -------
    Pandas dataframe
      A pandas dataframe containing topic coverages where every row
      corresponds to a specific RFC, identified by a row ID such as
      'RFC1234', and columns are topics and identified by names like
      't01' and 't11' to indicate 'Topic 1' and 'Topic 11', respectively.
    """

    fidx = metapy.index.make_forward_index('config.toml')

    # load `num_topics` topic model
    model = metapy.topics.TopicModel('models/lda-pgibbs-{}'.format(num_topics))

    # pattern objects needed for regex later
    p_rfc = re.compile(r'rfc(\d+).txt$')
    p_topic_coverage_idx = re.compile(r'(\d+): ')
    p_topic_coverage_val = re.compile(r': ([\d.]+)[,}]')

    # get a list of all pi values (topic coverage probabilities) of the corpus
    list_pi = []
    for doc_idx in range(fidx.num_docs()):
      # we need docid, e.g., RFC0001, to index documents
      path = fidx.metadata(doc_idx).get('path')
      docid = 'RFC' + p_rfc.search(path).group(1).zfill(4)

      # list of topics per document might miss leave out some so
      # we need to make sure we match indices with topic IDs and
      # set unmatched values, if any, to zeroes
      topic_dist_str = str(model.topic_distribution(doc_idx))
      topic_dist_idx = [int(s) for s in p_topic_coverage_idx.findall(topic_dist_str)]
      topic_dist_val = [float(s) for s in p_topic_coverage_val.findall(topic_dist_str)]
      # not all topics will have a probability value
      topic_dist_float = np.full(num_topics, -1.0)
      for i, val in enumerate(topic_dist_val):
          topic_dist_float[topic_dist_idx[i]] = val
      
      list_pi.append([docid] + list(topic_dist_float))

      # create pandas dataframe with topic coverage data
    column_names = ['docid']
    for i in range(1, num_topics + 1):
      column_names.append('t' + str(i).zfill(2))

    pi_df = pd.DataFrame(list_pi, columns=column_names)
    pi_df.sort_values(by='docid', inplace=True)
    pi_df.set_index('docid', inplace=True)

    return pi_df

  def get_topics(self, docid, num_topics=20, top_k=5, top_docs_per_topic=5):
    """
    Get the top k topics associated to the given `docid` and for each
    of those topics get the top 10 words describing that topic and the
    top number of docs for that specific topic including the
    corresponding metadata.
    
    Parameters
    ----------
    docid : str
      Document ID identifying the RFC such as RFC0001. It consists of
      the text 'RFC' followed by a four digit number including leading
      zeroes if any.

    num_topics : int
      Number of topics to be used in topic analysis. It will be used as
      part of the filename storing model parameters. Default: 20.

    top_k : int
      k in the top k topics that are associated to `docid`. Default: 3.

    top_docs_per_topic : int
      k in top k documents that exhibit the largest coverage for a
      selected topic. Default: 5.

    Returns
    -------
    dict
      Dictionary with the results consisting of three sections:
       * topics: Top k topics for the given `docid`.
       * words: Top 10 words for every top topic in topics.
       * docs: Docs with largest topic coverage for every top topic in topics
    """

    # if `docid` does not exist in pi_df return an empty dictionary
    if docid not in self.pi_df.index:
      return {}

    # get top k topics associated to `docid`
    topics = self.pi_df.loc[docid, :].\
             sort_values(ascending=False)[0:top_k].to_dict(into=OrderedDict)

    # get top words for every top k topic
    fidx = metapy.index.make_forward_index('config.toml')
    model = metapy.topics.TopicModel('models/lda-pgibbs-{}'.format(num_topics))
    # scorer allows to select high probability terms in a topic
    # that have lower probability in the other topics
    scorer = metapy.topics.BLTermScorer(model)
    words = OrderedDict()
    for topic in topics:
      # there was not probability assigned to this topic, so skip
      if topics[topic] == -1.0:
        continue
      tid = int(re.search(r'\d+$', topic).group()) - 1
      words[topic] = [{'word': fidx.term_text(pr[0]), 'p': pr[1]}
                     for pr in model.top_k(tid=tid, scorer=scorer)]

    # get top docs for every top k topic
    docs = OrderedDict()
    for topic in topics:
      top_k_docids = self.pi_df.loc[:, topic].\
                     sort_values(ascending=False)[0:top_docs_per_topic].\
                     to_dict(into=OrderedDict)
      metadata_list = []
      for top_k_docid, score in top_k_docids.items():
        metadata = self.get_metadata(top_k_docid)
        if metadata == {}:
          continue
        metadata['score'] = score
        metadata_list.append(metadata)
      docs[topic] = metadata_list

    return OrderedDict([('k', num_topics),
                        ('topics', topics),
                        ('words', words),
                        ('docs', docs)])
