import os
import fasta

def add_seq_adapters(fasta_path, start5_seq, end3_seq):
    
    file_root, file_ext = os.path.splitext(fasta_path)
    out_fasta_path = file_root + '_adapted' + file_ext
    n = 0
    
    with open(out_fasta_path, 'w') as out_file_obj:
        write = out_file_obj.write
    
        for head, seq in fasta.iter_fasta(fasta_path):
            seq = start5_seq + seq + end3_seq
            write(f'>{head}\n{seq}\n')
            n += 1
    
    print(f'Wrote {n:,} sequences to {out_fasta_path}')


if __name__ == '__main__':
    
    start5_seq = 'GTAGCTGGCCAGTCTGGCCAG'
    end3_seq   = 'GGAGGGCAGTCTGGGCAGTC'
    fasta_path = '../RCFrags_D2_UP000008816_L12_O4_Cecoli_standard_opt.fna'
    
    add_seq_adapters(fasta_path, start5_seq, end3_seq)
