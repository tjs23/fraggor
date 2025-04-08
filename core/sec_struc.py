import gzip, os, subprocess
import fasta

S4PRED_CMD = ['python3.9', '/home/tjs23/ext_gh/s4pred/run_model.py']

def predict_proteome_ss(proteome_fasta, working_dir):
    
    def get_up_name(head):
        
        db, acc, *other = head.split('|')
        
        return acc
    
    sub_dir =  proteome_fasta.split('.fasta')[0]
    
    file_obj = gzip.open(proteome_fasta, 'rt')
    
    data = fasta.read_fasta(file_obj, as_dict=False, head_processor=get_up_name)
    
    if not os.path.exists(working_dir):
        os.mkdir(working_dir)
    
    save_dir = os.path.join(working_dir, sub_dir)
    
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    
    n_seqs = len(data)
    
    for i, (name, seq) in enumerate(data):
        print(f'{i:,} of {n_seqs:,} : {name}', end = '\r')
        
        fasta_path = os.path.join(save_dir, f'{name}.fasta')
        lock_path = os.path.join(save_dir, f'{name}.lock')
        sstr_path = os.path.join(save_dir, f'{name}.ss2')
        
        if os.path.exists(sstr_path):
             continue

        if os.path.exists(lock_path):
             continue
        
        with open(lock_path, 'w') as file_obj:
             file_obj.write('LOCK\n')
        
        named_seqs = [(name, seq),]
        
        fasta.write_fasta(fasta_path, named_seqs, verbose=False)
                
        subprocess.call(S4PRED_CMD + [fasta_path], stdout=open(sstr_path, 'w'))
        
        if os.path.exists(lock_path):
                os.unlink(lock_path)
        
    
    print(f'{i:,} of {n_seqs:,}')
    
    
if __name__ == '__main__': 

    proteome_fasta = '../proteome_data/UP000008816_Staphylococcus_aureus.fasta'
    
    predict_proteome_ss(proteome_fasta, '../seq_sec_struc_data')

