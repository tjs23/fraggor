import os, sys, sqlite3, socket, subprocess, re
from functools import wraps

from datetime import datetime

import numpy as np

from flask import Flask, request, jsonify, render_template, session, send_from_directory, send_file

TABLE_SQL = """
CREATE TABLE FragDataSet (
  data_id INTEGER NOT NULL PRIMARY KEY,
  status VARCHAR(32) NOT NULL,
  proteome VARCHAR(64) NOT NULL,
  date_day INT NOT NULL,
  date_month INT NOT NULL,
  date_year INT NOT NULL,
  codon_use VARCHAR(128) NOT NULL,
  num_prots INT,
  num_seqs INT,
  pep_len INT NOT NULL,
  overlap INT NOT NULL,
  taxon_id INT NOT NULL,
  taxon_name VARCHAR(512) NOT NULL,
  taxon_lineage TEXT
);
"""

PROTEOME_KEYS =  ('uniprot_id', 'species', 'taxon_id', 'num_prots', 'completeness')
DATASET_KEYS = ('data_id', 'proteome_id', 'species', 'taxon_id', 'proteome', 'num_prots', 'status', 'num_seqs', 'pep_len', 'overlap', 'codon_use', 'date')


"""
Try GPU for SS

LATER
Add taxon lineage as embedded pulldown
? Fail if too many jobs waiting?
"""


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
APP_TITLE = 'Peptide Fragment Generator'
#SITE_SUBDIR = '/fraggor'
SITE_SUBDIR = ''
SQLITE3_DB_PATH = os.path.join(BASE_DIR, 'fraggor_01.sqlite3')

sys.path.append(os.path.join(BASE_DIR, 'core'))

from proteome import get_uniprot_clade_proteome_info, get_proteome_info
from agent import JOB_DIR, RUN_DIR, RESULT_DIR, AGENT_PATH
from fasta import count_fasta

app = Flask(__name__)
app.secret_key = '1c487v9qty72tycw47tfjsdgcgmlA0wfwvA8e8jh'
app.config.update(SESSION_COOKIE_SECURE=False, ## True, for SSL deploy
                  SESSION_COOKIE_HTTPONLY=True,
                  SESSION_COOKIE_SAMESITE='Strict',
                  MAX_FORM_MEMORY_SIZE=100 * 1024, # 100k
                  MAX_FORM_PARTS=100)

if socket.gethostbyname(socket.gethostname()) not in ("127.0.1.1","127.0.0.1"):
    app.config['APPLICATION_ROOT'] = SITE_SUBDIR


@app.after_request
def add_header(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response


#START THE CALC AGENT
if not os.path.exists(AGENT_PATH):
    #   os.unlink(AGENT_PATH)
    CMD = ['nice', '-9', 'python3', os.path.join(BASE_DIR, 'core', 'agent.py')]
    proc = subprocess.Popen(CMD)
   

def get_data_file_root(data_id, proteome, pep_len, overlap, codon_use):

    return f'RCFrags_D{data_id}_{proteome}_L{pep_len}_O{overlap}_C{codon_use}'


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(TABLE_SQL)
    
    data_id = 1
    placeholder = ', '.join(['?'] * 14)
    smt = f'INSERT INTO FragDataSet (data_id, status, proteome, date_day, date_month, date_year, codon_use, num_prots, num_seqs, pep_len, overlap, taxon_id, taxon_name, taxon_lineage) VALUES ({placeholder});'
    
    for file_name in os.listdir(RESULT_DIR):
        if file_name.endswith('.fasta'):
            file_path = os.path.join(RESULT_DIR, file_name)
            file_root = os.path.splitext(file_name)[0]
            path_root = os.path.join(RESULT_DIR, file_root)
            
            if os.path.exists(path_root + '.fna') and os.path.exists(path_root + '_opt.fna'):
                match = re.match('RCFrags_D(\d+)_(UP\d+)_L(\d+)_O(\d+)_C(\w+)', file_root)
                
                if match:
                    #data_id = match.group(1)
                    proteome = match.group(2)
                    pep_len = match.group(3)
                    overlap = match.group(4)
                    codon_use = match.group(5)
                    num_seqs = count_fasta(file_path)
                    upid, species, tax_id, tax_lineage, num_prots, completeness = get_proteome_info(proteome)
                    date = datetime.fromtimestamp(os.path.getmtime(file_path))
                    row_data = (data_id, 'complete', upid, date. day, date.month, date.year, codon_use, num_prots, num_seqs, pep_len, overlap, tax_id, species, tax_lineage)
                    cursor.execute(smt, row_data)
                    data_id += 1

    conn.commit()
    conn.close()

    
class SQLCursor(object):
 
    def __init__(self, smt=None, data=None):
        self.smt = smt
        self.conn = None
        self.data = data
        
    def __enter__(self):

        if not os.path.exists(SQLITE3_DB_PATH):
            init_db(SQLITE3_DB_PATH)
        
        self.conn = sqlite3.connect(SQLITE3_DB_PATH)            
        self.cursor = self.conn.cursor()
       
        if self.smt:
            if self.data:
                if isinstance(self.data, list):
                    data = tuple(self.data)
                elif isinstance(self.data, tuple):
                    data = self.data
                else:
                    data = (self.data,)
                
                self.cursor.execute(self.smt, data)
            else:
                self.cursor.execute(self.smt)
 
        return self.cursor

    def __exit__(self, exc_class, exc, traceback):
       
       self.conn.close()



       
def json_data(func):

    @wraps(func)
    def wrapper(*args, **kwargs):        
        return func(request.get_json(), *args, **kwargs)
                   
    return wrapper
  
    
def _sanitize_name(text):
 
  text = text.strip()
  transtab = str.maketrans('\"{[}]\t\n\r', "\'(())   ", '\b\f!$%^&*+=;:@~#<>/?|\\') 
  text = text.translate(transtab)
  text = ' '.join(text.split())
  
  return text    


def _sanitize_email(text):
  
  if text.count('@') == 1:
     a, b = text.split('@')
     return _sanitize_name(a) + '@' + _sanitize_name(b)
  
  else:
     return ''
     
@app.route('/set_proteome/', methods=['POST','GET'])
@json_data
def set_proteome(json_data):    
    session['proteome'] = json_data['proteome']    
    return jsonify({})

@app.route('/set_data_id/', methods=['POST','GET'])
@json_data
def set_data_id(json_data):    
    session['data_id'] = json_data['data_id']    
    return jsonify({})


@app.route('/download_data/<seq_type>', methods=['POST','GET'])
def download_data(seq_type):        
    # seq_type '.fasta', '_opt.fna' or '.fna'
    
    file_name = None
    
    if 'data_id' in session:       
        data_id = session['data_id']
        
        with SQLCursor('SELECT proteome, pep_len, overlap, codon_use FROM FragDataSet WHERE data_id = ?;', (data_id,)) as cursor:
            result = cursor.fetchone()
            
            if result:
                proteome, pep_len, overlap, codon_use = result     
                file_root = get_data_file_root(data_id, proteome, pep_len, overlap, codon_use)
                file_name = file_root + seq_type
    
    if file_name:            
        return send_from_directory(RESULT_DIR, file_name)

    else:
        return ('', 204)
        
             
@app.route('/get_proteome_table/', methods=['POST','GET'])
@json_data
def get_proteome_table(json_data):  

   rows = []
   
   if ('proteome' in session) and session['proteome']:
       upid, species, tax_id, tax_lineage, count, completeness = get_proteome_info(session['proteome'])
       row = (upid, species, tax_id, count, completeness)
       row_dict = dict(zip(PROTEOME_KEYS, row))
       rows.append(row_dict)

   return jsonify({'rows':rows})


@app.route('/get_proteome_cols/', methods=['POST','GET'])
@json_data
def get_proteome_cols(json_data):
    
    codon_set = 'ecoli_standard'
    heads = ('UniProt ID', 'Species/strain', 'Taxon ID', 'Size', '% Completeness')
    cols = [{'title':head, 'field':key} for head, key in zip(heads, PROTEOME_KEYS)]
    
    codon_sets = [{'value':codon_set, 'label':'E.coli standard'}]
    
    return jsonify({'cols':cols,'codon_set':codon_set, 'codon_sets':codon_sets})


@app.route('/search_taxon/', methods=['POST','GET'])
@json_data
def search_taxon(json_data):
    
    taxon = _sanitize_name(json_data['taxon']).strip()
    error = None
    rows = []
    keys =  ('uniprot_id', 'species', 'taxon_id', 'num_prots', 'completeness')
    
    if not taxon:
        name = json_data['taxon']
        error = f'Invalid taxon name "{name}"'
    
    else:
        proteome_list = get_uniprot_clade_proteome_info(taxon, top=1000, verbose=False)
        
        for completeness, upid, species, tax_id, tax_lineage, count in proteome_list:
            row = (upid, species, tax_id, count, completeness)
            row_dict = dict(zip(PROTEOME_KEYS, row))
            rows.append(row_dict)
        
    return jsonify({'error':error, 'rows':rows})
 
 
@app.route('/check_generate_data/', methods=['POST','GET'])
@json_data
def check_generate_data(json_data):
 
    proteome = json_data['proteome']
    overlap = int(json_data['overlap'])
    pep_len = int(json_data['pep_len'])
    codon_use = json_data['codon_set']
    email = _sanitize_email(json_data['email']).lower().strip()
    
    msg = None
    error = None
    params = {}
    
    if not email:
        error = 'Not a valid email address'
     
    else:
        info = get_proteome_info(proteome)
 
        if info:
            params = {'proteome':proteome, 'overlap':overlap, 'pep_len':pep_len, 'codon_use':codon_use, 'email':email}
            msg = f'<p>Job is for proteome "{proteome}"</p><p>Using peptide length {pep_len}, overlap {overlap} and codons "{codon_use}"</p><p>A notification will be sent to "{email}" upon completion.</p>'
 
        else:
            error = f'UniProt proteome ID "{proteome}" generated an invalid response'        

    return jsonify({'error':error, 'msg':msg, 'params':params})
   
  
@app.route('/generate_data/', methods=['POST','GET'])
@json_data
def generate_data(json_data):
    
    proteome = json_data['proteome']
    overlap = int(json_data['overlap'])
    pep_len = int(json_data['pep_len'])
    codon_use = json_data['codon_use']
    email = _sanitize_email(json_data['email'])
    
    upid, species, tax_id, tax_lineage, num_prots, completeness = get_proteome_info(proteome)
 
    with SQLCursor('SELECT MAX(data_id) FROM FragDataSet;') as cursor:
        data_id, = cursor.fetchone()
        if data_id:
            data_id += 1
        else:
            data_id = 1
 
    today = datetime.today()
    day = today.day
    month = today.month
    year = today.year
 
    row_data = (data_id, 'pending', upid, day, month, year, codon_use, num_prots, pep_len, overlap, tax_id, species, tax_lineage)
    placeholder = ', '.join(['?' for x in row_data])
    smt = f'INSERT INTO FragDataSet (data_id, status, proteome, date_day, date_month, date_year, codon_use, num_prots, pep_len, overlap, taxon_id, taxon_name, taxon_lineage) VALUES ({placeholder});'
    with SQLCursor(smt, row_data) as cursor:
        cursor.connection.commit()
 
    job_file = f'{data_id}_{proteome}.job'
    job_path = os.path.join(JOB_DIR, job_file)
 
    with open(job_path, 'w') as out_file_obj:
        out_file_obj.write(f'{data_id}\t{proteome}\t{species}\t{codon_use}\t{pep_len}\t{overlap}\t{email}\n')
     
    return jsonify({})   
   
   
@app.route('/get_data_cols/', methods=['POST','GET'])
@json_data
def get_data_cols(json_data):

    heads = ('ID', 'Proteome ID', 'Species', 'Taxon ID', 'Proteome', 'Protein<br>Seqs', 'Status', 'Peptide<br>Seqs', 'Peptide<br>length', 'Overlap<br>length', 'Codon use', 'Compiled on')
    
    cols = [{'title':head, 'field':key} for head, key in zip(heads, DATASET_KEYS)]
    cols[1]['visible'] = False
    cols[3]['formatter'] = "html"
    cols[4]['formatter'] = "html"
    
    return jsonify({'cols':cols,})
   

@app.route('/get_data_table/', methods=['POST','GET'])
@json_data
def get_data_table(json_data):
    
    status_updates = []
    count_updates = []
    delete_old_fails = []
    rows = []
    
    with SQLCursor(f'SELECT data_id, status, proteome, date_day, date_month, date_year, codon_use, num_prots, num_seqs, pep_len, overlap, taxon_id, taxon_name FROM FragDataSet;') as cursor:
        for data_id, status, proteome, date_day, date_month, date_year, codon_use, num_prots, num_seqs, pep_len, overlap, taxon_id, taxon_name in cursor:
            date = datetime(date_year, date_month, date_day)
            
            if status == 'complete':
                if not num_seqs:
                    file_root = get_data_file_root(data_id, proteome, pep_len, overlap, codon_use)
                    fasta_path = os.path.join(RESULT_DIR, file_root + '.fasta')
                    num_seqs = count_fasta(fasta_path)
                    count_updates.append((data_id, num_seqs))
            
            else:
                file_root = get_data_file_root(data_id, proteome, pep_len, overlap, codon_use)
                fasta_path = os.path.join(RESULT_DIR, file_root + '.fasta')
                pend_path = os.path.join(JOB_DIR, f'{data_id}_{proteome}.job')
                job_path = os.path.join(RUN_DIR, f'{data_id}_{proteome}.job')
                
                if os.path.exists(fasta_path):
                    num_seqs = count_fasta(fasta_path)
                    count_updates.append((data_id, num_seqs))
                    status = 'complete'
                
                elif os.path.exists(job_path):
                    status = 'running'

                elif os.path.exists(pend_path):
                    status = 'pending'
                    
                else:
                    delta = datetime.today() - date
                    
                    if delta.days >= 1:
                        delete_old_fails.append(data_id)
                        continue
                    
                    status = 'failed'    
               
                status_updates.append((data_id, status))   
            
            taxon_html = f'<a href="https://www.uniprot.org/taxonomy/{taxon_id}">{taxon_id}</a>'
            proteome_html = f'<a href="https://www.uniprot.org/proteomes/{proteome}">{proteome}</a>'
            row = [data_id, proteome, taxon_name, taxon_html, proteome_html, num_prots, status, num_seqs, pep_len, overlap, codon_use, date.strftime('%d/%b/%Y')]
            row_dict = dict(zip(DATASET_KEYS, row))
            rows.append(row_dict)

    for data_id in delete_old_fails:
        with SQLCursor(f'DELETE FROM FragDataSet WHERE data_id = ?;', (data_id,)) as cursor:
            cursor.connection.commit()
    
    for data_id, status in status_updates:
        with SQLCursor(f'UPDATE FragDataSet SET status=? WHERE data_id = ?;', (status, data_id)) as cursor:
            cursor.connection.commit()

    for data_id, num_seqs in count_updates:
        with SQLCursor(f'UPDATE FragDataSet SET num_seqs=? WHERE data_id = ?;', (num_seqs, data_id)) as cursor:
            cursor.connection.commit()
                        
    return jsonify({'rows':rows})
  
  
@app.route('/', methods=['POST','GET'])
def main():
    return render_template('main.html', ssd=SITE_SUBDIR)

@app.route('/calc', methods=['POST','GET'])
def calc():
    return render_template('calc.html', ssd=SITE_SUBDIR)

@app.route('/about', methods=['POST','GET'])
def about():
    return render_template('about.html', ssd=SITE_SUBDIR)
           
       
