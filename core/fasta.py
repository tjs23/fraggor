import re, time, random, string

FASTA_TMP_PATH = '__fasta_temp__'
FASTA_SEQ_LINE = re.compile('(\S{59})(\S)')
FASTA_TRANS_TABLE = str.maketrans('JOBZU*', 'CPXXXX')
RNA_TRANS_TABLE = str.maketrans('U', 'T')

def _get_rand_string(size):

    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(size))
    
    
def temp_fasta_file_path(headerd_seqs):

    file_path = '%s_%.3f%s%s' % (FASTA_TMP_PATH, time.time(), _get_rand_string(8), '.fasta')
    write_fasta(file_path, headerd_seqs)
    
    return file_path


def fasta_item(header, seq, end=''):

    seq = seq.replace(u'\ufffd', '')
    seq = seq.upper()
    seq = re.sub('\s+','',seq)
    seq = seq[0] + FASTA_SEQ_LINE.sub(r'\1\n\2',seq[1:])
 
    return '>%s\n%s%s' % (header, seq, end) 


def fasta_string(headerd_seqs):

    if isinstance(headerd_seqs, dict):
        headerd_seqs = headerd_seqs.items()

    entries = [fasta_item(header, seq) for header, seq in headerd_seqs]

    return '\n'.join(entries)


def count_fasta(file_path):

    num_seqs = 0
    with open(file_path, buffering=2**16) as file_obj:
        for line in file_obj:
            if line[0] == '>':
                num_seqs += 1
                
    return num_seqs
                

def write_fasta(file_path, headerd_seqs, verbose=True):
    
    if isinstance(headerd_seqs, dict):
        headerd_seqs = list(headerd_seqs.items())
    
    n = 0
    with open(file_path, 'w') as file_obj:
        write = file_obj.write

        for header, seq in headerd_seqs:
            write('%s\n' % fasta_item(header, seq) )
            n += 1
    
    if verbose:
         print(f'Written {n:,} sequences to {file_path}')


def iter_fasta(path):
  
    seq = []
    header = None
    
    for line in open(path):
        line = line.strip()
        
        if not line:
            continue
        
        if line[0] == '>':
            if header:
                yield (header, ''.join(seq).translate(RNA_TRANS_TABLE))

            seq = []
            header = line[1:]
        
        elif header:
            seq.append(line)
    
    if header:
        yield (header, ''.join(seq).translate(RNA_TRANS_TABLE))
    


def read_fasta(stream_or_path, as_dict=True, head_processor=None):
    
    if isinstance(stream_or_path, str):
        stream = open(stream_or_path)
    elif isinstance(stream_or_path, (list, tuple)):
        stream = stream_or_path
    else:
        stream = stream_or_path
    
    headerd_seqs = []
    append = headerd_seqs.append
    header = None
    seq = []

    for line in stream:
        line = line.strip()
        
        if not line:
            continue
        
        if line[0] == '>':
            if header:
                append((header, ''.join(seq).translate(FASTA_TRANS_TABLE)))

            seq = []
            header = line[1:]
            
            if head_processor:
                header = head_processor(header)
        
        elif header:
            seq.append(line)

    if header:
        append((header, ''.join(seq).translate(FASTA_TRANS_TABLE)))

    if as_dict:
        return dict(headerd_seqs)
        
    else:
        return headerd_seqs

    
