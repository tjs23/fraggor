import gzip, os, subprocess
import fasta

S4PRED_CMD = ['python3.9', '/home/tjs23/ext_gh/s4pred/run_model.py'] # , '--device', 'gpu']

def predict_proteome_ss(proteome_fasta, working_dir, verbose=True, overwite=False):
    
    def get_up_name(head):
        
        db, acc, *other = head.split('|')
        
        return acc
    
    proteome_ss = os.path.splitext(proteome_fasta)[0] + '.ss'
    
    if os.path.exists(proteome_ss) and not overwite:
        if verbose:
            print(f'Found existing {proteome_ss}')
        return proteome_ss
    
    sub_dir =  proteome_fasta.split('.fasta')[0]
    
    #file_obj = gzip.open(proteome_fasta, 'rt')
    file_obj = open(proteome_fasta, 'r')
    
    data = fasta.read_fasta(file_obj, as_dict=False, head_processor=get_up_name)
    
    if not os.path.exists(working_dir):
        os.mkdir(working_dir)
    
    save_dir = os.path.join(working_dir, sub_dir)
    
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    
    n_seqs = len(data)
    sstr_paths = []
    fasta_paths = []
    
    for i, (name, seq) in enumerate(data):
        if True: # verbose:
            print(f'{i:,} of {n_seqs:,} : {name}', end = '\r')
        
        fasta_path = os.path.join(save_dir, f'{name}.fasta')
        lock_path = os.path.join(save_dir, f'{name}.lock')
        sstr_path = os.path.join(save_dir, f'{name}.ss2')
        sstr_paths.append(sstr_path)
        fasta_paths.append(fasta_path)
        
        if os.path.exists(sstr_path):
            line = None
            # Check
            with open(sstr_path) as file_obj:
                head1 = file_obj.readline()
                head2 = file_obj.readline()
                for line in file_obj:
                    line = line.strip()
                    break
                 
            if line:
               continue
               
            else:
               os.unlink(sstr_path)

        if os.path.exists(lock_path):
             continue
        
        with open(lock_path, 'w') as file_obj:
             file_obj.write('LOCK\n')
        
        named_seqs = [(name, seq),]
        
        fasta.write_fasta(fasta_path, named_seqs, verbose=False)
                
        subprocess.call(S4PRED_CMD + [fasta_path], stdout=open(sstr_path, 'w'))
                    
        
        if os.path.exists(lock_path):
            os.unlink(lock_path)
    
    if True: # verbose:
        print(f'{i:,} of {n_seqs:,}')
    
    with open(proteome_ss, 'w') as out_file_obj:
        
        for ss_path in sstr_paths:
            with open(ss_path) as file_obj:
                pid = os.path.basename(ss_path)[:-4]
 
                head1 = file_obj.readline()
                head2 = file_obj.readline()
                seq = []
                ss = []
                start_num = None
                prev_num = None
 
                for line in file_obj:
                    line = line.strip()
 
                    if line:
                        res_num, res_olc, res_ss, *scores = line.split()
                        res_num = int(res_num)
 
                        if start_num is None:
                            start_num = res_num
                            prev_num = res_num
                        else:
                            while res_num != (prev_num+1):
                                seq.append('-')
                                ss.append('-')
                                res_num += 1
 
                            prev_num = res_num
                            
                        seq.append(res_olc)
                        ss.append(res_ss)
 
                ss = ''.join(ss)
                seq = ''.join(seq)
                        
            out_line = f'{pid} {start_num} {seq} {ss}\n'
            out_file_obj.write(out_line)
        
    for ss_path in sstr_paths:
        os.unlink(ss_path)
 
    for fasta_path in fasta_paths:
        os.unlink(fasta_path)
    
    if verbose:
        print(f'Wrote {proteome_ss}')
            
    return proteome_ss
    
    
if __name__ == '__main__': 

    proteome_fasta = '../proteome_data/UP000008816_Staphylococcus_aureus.fasta'
    
    predict_proteome_ss(proteome_fasta, '../seq_sec_struc_data')

