import requests
import logging
from path import Path

from baleen.utils import file_list, make_dir

log = logging.getLogger(__name__)

# silence request logging
logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(
    logging.WARNING)


def query_solr(solr_url, core, doi, fields=[]):
    url = '/'.join([solr_url.rstrip('/'), core, 'select'])
    params = {'q': 'doi:"' + doi + '"',
              'wt': 'json'}

    if fields:
        params['fl'] = ','.join(f for f in fields)

    response = requests.get(url, params)

    json = response.json()

    if json['response']['docs']:
        return json['response']['docs'][0]
    else:
        log.error('DOI {!r} not found in core {!r}'.format(doi, core))


def get_text(core, doi, fields, hash_tags, resume, solr_url, text_dir):
    prefix, suffix = doi.split('/')
    text_fname = '#'.join([prefix, suffix] + hash_tags) + '.txt'
    text_path = Path(text_dir) / text_fname

    if resume and text_path.exists() :
        log.info('skipping file {!r} because it exists'.format(text_path))
    else:
        doc = query_solr(solr_url, core, doi, fields)
        values = []
        for key in fields:
            try:
                val = doc[key]
            except KeyError as key:
                log.error('no {!r} field for doi {!r}'.format(key.args[0], doi))
                return
            # flatten list values, e.g. for fulltext
            if isinstance(val, list):
                values.append('\n'.join(val))
            else:
                values.append(val)
        text = '\n\n'.join(values)
        log.info('creating text file {!r}'.format(text_path))
        text_path.write_text(text)


def get_texts(doi_files, solr_url, fields, text_dir, hash_tags=[],
              resume=False, max_n=None):
    Path(text_dir).makedirs_p()
    n = 0

    for doi_fname in file_list(doi_files):
        log.info('getting text sources from {!r}'.format(doi_fname))
        for line in open(doi_fname):
            try:
                core, doi = line.split()
            except:
                log.error('ill-formed line in file {!r}:\n'
                          '{}'.format(doi_fname, line))
                continue

            get_text(core, doi, fields, hash_tags, resume, solr_url, text_dir)
            n += 1
            if n == max_n:
                log.info('reached max_n={}'.format(n))
                break


def get_full_text(doi_files, solr_url, text_dir, hash_tags=['full'],
                  resume=False):
    get_texts(doi_files, solr_url, ['title', 'abstract', 'fulltext'], text_dir,
              hash_tags=hash_tags, resume=resume)


def get_abs_text(doi_files, solr_url, text_dir, hash_tags=['abs'],
                 resume=False, max_n=None):
    """
    get text of abstracts

    :param doi_files:
    :param solr_url:
    :param text_dir:
    :param hash_tags:
    :param resume:
    :return:
    """
    get_texts(doi_files, solr_url, ['title', 'abstract'], text_dir,
              hash_tags=hash_tags, resume=resume, max_n=max_n)




def get_solr_sources(xml_files, in_dir):
    '''
    Convert output of IR step (article sources in XMl format)
    to Megamouth input files (tab-separated text file where each line contains
    the name of a Solr core and the DOI of a source article).
    '''
    in_dir = Path(in_dir)
    in_dir.makedirs_p()

    for xml_file in file_list(xml_files):
        name =  Path(xml_file).name
        # arbitrary mapping from filenames to Solr cores
        if name.startswith('elsevier'):
            core = 'data-scientific'
        elif name.startswith('macmillan'):
            core = 'nature-art'
        elif name.startswith('wiley'):
            core = 'wiley-art'
        elif name.startswith('springer'):
            core = 'springer-art'
        else:
            raise ValueError('undefined core for file ' + xml_file)

        tsv_file = in_dir + '/' + Path(xml_file).name + '.tsv'

        # XML is ill-formed (incomplete entities etc.)
        # so do not use an XML parser
        with open(xml_file) as inf, open(tsv_file, 'w') as outf:
            log.info('creating ' + tsv_file)

            for line in inf:
                if line.lstrip().startswith('<doi>'):
                    doi = '/'.join(line.split('<')[-2].split('/')[-2:])
                    print(core, doi, sep='\t', file=outf)