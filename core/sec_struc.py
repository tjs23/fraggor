import time, os, subprocess, multiprocessing, sys, gc, psutil
import fasta

MAX_CORES = multiprocessing.cpu_count()
NEWLINE_CHARS = 0
KEYBOARD_INTERRUPT_MSG = 'Parallel jobs stopped - KeyboardInterrupt'
PROG_CHARS = ('#', '-')

S4PRED_CMD = ['python3.10', '/home/tjs23/ext_gh/s4pred/run_model.py', '--device', 'gpu']

# Could sort jobs by creation time

def report(msg, line_return=False):
  global NEWLINE_CHARS

  if line_return:
    fmt = '\r%%-%ds' % max(NEWLINE_CHARS, len(msg))
    sys.stdout.write(fmt % msg) # Must have enouch columns to cover previous msg
    sys.stdout.flush()
    NEWLINE_CHARS = len(msg)
    
  else: 
    if NEWLINE_CHARS:
      print('')
    print(msg)
    NEWLINE_CHARS = 0
    

def info(msg, line_return=False):

  report('INFO: ' + msg, line_return)
  
 
def warn(msg):

  report('WARN: ' + msg)


def critical(msg):

  report('EXIT: ' + msg)
  report('STOP')
  sys.exit(0)


def progress(i, n):

  pc = (100.0*i)/n
  prog = int(pc)
  msg = '    |{}{}|{:7.2f}% [{:,}]'.format(PROG_CHARS[0] * prog, PROG_CHARS[1] * (100-prog), pc, n)
  report(msg, True)


def _parallel_job_wrapper(job, out_queue, target_func, data_item, args, kw):

    try:
        result = target_func(data_item, *args, **kw)
        out_queue.put((job, result), False)
 
    except KeyboardInterrupt as err: # Ignore in multiple sub-processes as this will be picked up only once later
        return
        

def parallel_run(target_func, job_data, common_args=(), common_kw={},
                 num_cpu=MAX_CORES, verbose=True, local_cpu_arg=None):
    # This does not use Pool.apply_async because of its inability to pass
    # pickled non-global functions
    
    from multiprocessing import Process, Manager
        
    job_data = [x for x in job_data if x]
    num_jobs = len(job_data)
    num_proc = min(num_cpu, num_jobs)
    procs = {} # Current processes
    queue = Manager().Queue() # Queue() # Collect output
    results = [None] * num_jobs
    gc.collect() # Mimimise mem footprint before fork
    
    if verbose:
        msg = 'Running {} for {:,} tasks on {:,} cores'
        info(msg.format(target_func.__name__, num_jobs, num_proc))
    
    k = 0
    prev = 0.0
    
    for j in range(num_jobs):
        
        if len(procs) == num_proc: # Full
            try:
                i, result = queue.get()
 
            except KeyboardInterrupt:
                critical(KEYBOARD_INTERRUPT_MSG)

            results[i] = result
            del procs[i]
            
            if verbose:
                k += 1
                f = k / float(num_jobs)
                
                if (f-prev) > 0.001: # Avoid very fine updates
                    progress(k, num_jobs)
                    prev = f
        
        if local_cpu_arg and (j >= num_proc): # After initial allocations
            arg, default = local_cpu_arg
            cpu_free = 1.0 - (psutil.cpu_percent()*0.01)
            kw_args = dict(common_kw)
            kw_args[arg] = max(default, int(cpu_free*num_proc*0.5))
        else:
            kw_args = common_kw
                
        args = (j, queue, target_func, job_data[j], common_args, kw_args)
        proc = Process(target=_parallel_job_wrapper, args=args)
        procs[j] = proc

        try:
            proc.start()
        
        except IOError:
            time.sleep(0.01)
            proc.start()

        except KeyboardInterrupt:
            critical(KEYBOARD_INTERRUPT_MSG)
            
        except Exception as err:
            raise(err)
            
    # Last waits
    
    while procs:
        try:
            i, result = queue.get()
            
        except KeyboardInterrupt:
            critical(KEYBOARD_INTERRUPT_MSG)
        
        results[i] = result
        del procs[i]
     
        if verbose:
            k += 1
            progress(k, num_jobs)
 
    if verbose:
        print('')
 
    #queue.close()
 
    return results


def predict_proteome_ss(proteome_fasta, working_dir, verbose=True, overwite=False, num_parallel=8):
    
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
    
    temp_dir = os.path.join(working_dir, sub_dir)
    
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)
    
    
    def predict_ss(job_args):
        
        fasta_path, sstr_path = job_args
       
        subprocess.call(S4PRED_CMD + [fasta_path], stdout=open(sstr_path, 'w'))
        
        if not os.path.exists(sstr_path):
            subprocess.call(S4PRED_CMD + [fasta_path], stdout=open(sstr_path, 'w'))
    
    
    n_seqs = len(data)
    sstr_paths = []
    fasta_paths = []
    job_data = []
    
    for i, (name, seq) in enumerate(data):
        if True: # verbose:
            print(f'{i:,} of {n_seqs:,} : {name}', end = '\r')
        
        fasta_path = os.path.join(temp_dir, f'{name}.fasta')
        lock_path = os.path.join(temp_dir, f'{name}.lock')
        sstr_path = os.path.join(temp_dir, f'{name}.ss2')
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
                 
            if not line:
               os.unlink(sstr_path)
               
        if os.path.exists(sstr_path):
            if os.path.exists(lock_path):
                os.unlink(lock_path)
                
            continue

        #if os.path.exists(lock_path):
        #     continue
        
        #with open(lock_path, 'w') as file_obj:
        #     file_obj.write('LOCK\n')
        
        named_seqs = [(name, seq),]
        
        fasta.write_fasta(fasta_path, named_seqs, verbose=False)
        #job_data.append((fasta_path, sstr_path))
                       
        subprocess.call(S4PRED_CMD + [fasta_path], stdout=open(sstr_path, 'w'))
        
        if not os.path.exists(sstr_path):
            subprocess.call(S4PRED_CMD + [fasta_path], stdout=open(sstr_path, 'w'))

        #if os.path.exists(lock_path):
        #    os.unlink(lock_path)
   
    if True: # verbose:
        print(f'{i:,} of {n_seqs:,}')
        
    #parallel_run(predict_ss, job_data, num_cpu=num_parallel, verbose=True)   
     
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
        
    #for ss_path in sstr_paths:
    #    os.unlink(ss_path)
 
    for fasta_path in fasta_paths:
        os.unlink(fasta_path)
    
    #os.unlink(temp_dir)
    
    if verbose:
        print(f'Wrote {proteome_ss}')
            
    return proteome_ss
    
    
if __name__ == '__main__': 

    proteome_fasta = '../proteome_data/UP000008816_Staphylococcus_aureus.fasta'
    
    predict_proteome_ss(proteome_fasta, '../seq_sec_struc_data')

