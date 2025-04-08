import re, time, random, string

FASTA_TMP_PATH = '__fasta_temp__'
FASTA_SEQ_LINE = re.compile('(\S{59})(\S)')
FASTA_TRANS_TABLE = str.maketrans('JOBZU*', 'CPXXXX')


def _get_rand_string(size):

    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(size))
    
    
def temp_fasta_file_path(named_seqs):

    file_path = '%s_%.3f%s%s' % (FASTA_TMP_PATH, time.time(), _get_rand_string(8), '.fasta')
    write_fasta(file_path, named_seqs)
    
    return file_path


def fasta_item(name, seq, end=''):

    seq = seq.replace(u'\ufffd', '')
    seq = seq.upper()
    seq = re.sub('\s+','',seq)
    seq = seq[0] + FASTA_SEQ_LINE.sub(r'\1\n\2',seq[1:])
 
    return '>%s\n%s%s' % (name, seq, end) 


def fasta_string(named_seqs):

    if isinstance(named_seqs, dict):
        named_seqs = named_seqs.items()

    entries = [fasta_item(name, seq) for name, seq in named_seqs]

    return '\n'.join(entries)


def write_fasta(file_path, named_seqs, verbose=True):
    
    if isinstance(named_seqs, dict):
        named_seqs = list(named_seqs.items())
    
    n = 0
    with open(file_path, 'w') as file_obj:
        write = file_obj.write

        for name, seq in named_seqs:
            write('%s\n' % fasta_item(name, seq) )
            n += 1
    
    if verbose:
         print(f'Written {n:,} sequences to {file_path}')


def read_fasta(stream_or_path, as_dict=True, head_processor=None):
    
    if isinstance(stream_or_path, str):
        stream = open(stream_or_path)
    elif isinstance(stream_or_path, (list, tuple)):
        stream = stream_or_path
    else:
        stream = stream_or_path
    
    named_seqs = []
    append = named_seqs.append
    name = None
    seq = []

    for line in stream:
        line = line.strip()
        
        if not line:
            continue
        
        if line[0] == '>':
            if name:
                append((name, ''.join(seq).translate(FASTA_TRANS_TABLE)))

            seq = []
            name = line[1:]
            
            if head_processor:
                name = head_processor(name)
        
        elif name:
            seq.append(line)

    if name:
        append((name, ''.join(seq).translate(FASTA_TRANS_TABLE)))

    if as_dict:
        return dict(named_seqs)
        
    else:
        return named_seqs

    
