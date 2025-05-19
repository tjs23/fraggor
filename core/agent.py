import os, atexit, time, smtplib
from time import sleep

from proteome import download_uniprot_proteome_fasta
from sec_struc import predict_proteome_ss
from frag_gen import get_random_coil_frags


DIR = os.path.dirname(__file__)
JOB_DIR = os.path.join(DIR, 'jobs/pending/')
RUN_DIR = os.path.join(DIR,'jobs/running/')
RESULT_DIR = os.path.join(DIR, 'fragment_data/')
AGENT_PATH = os.path.join(DIR, 'AGENT_LOCK')
SMTP_SERVER = 'mail.mrc-lmb.cam.ac.uk'      
FROM_ADDR = 'tstevens@mrc-lmb.cam.ac.uk'     

# Could sort jobs by creation time

def make_rc_fragments(data_id, proteome_uid, species, codon_use, pep_len, overlap, save_dir):
   
    proteome_fasta_path = download_uniprot_proteome_fasta(species, proteome_uid, verbose=False)

    proteome_ss_path = predict_proteome_ss(proteome_fasta_path, '../seq_sec_struc_data', verbose=False)
    
    path_prefix = f'D{data_id}_U{proteome_uid}'
    
    get_random_coil_frags(proteme_ss_path, path_prefix, save_dir, pep_len, overlap, codon_use, verbose=True)


def cleanup_agent():

    os.unlink(AGENT_PATH)


def start_agent(wait_interval=5):
    
    if os.path.exists(AGENT_PATH):
        raise Exception(f'Agent lock file "{AGENT_PATH}" present, possibly from an unclean shut-down. Remove this before retrying.')
    
    with open(AGENT_PATH, 'w') as file_obj:
        start_time = time.asctime(time.localtime())
        file_obj.write(f'LOCK {start_time}\n')
    
    atexit.register(cleanup_agent)    
    
    aborted = os.listdir(RUN_DIR)
    for file_name in aborted:
        if file_name.endswith('.job'):
            run_path = os.path.join(RUN_DIR, file_name)
            os.unlink(run_path)
            print(f'Removed aborted job "{run_path}"')
        
    while os.path.exists(AGENT_PATH):
        jobs = os.listdir(JOB_DIR)
        
        for file_name in jobs:
            if file_name.endswith('.job'):
                run_path = os.path.join(RUN_DIR, file_name)
                job_path = os.path.join(JOB_DIR, file_name)
                
                with open(job_path) as file_obj, open(run_path, 'w') as out_file_obj:
                   out_file_obj.write(file_obj.read())
                   
                os.unlink(job_path)   
                
                with open(run_path) as file_obj:
                   data = file_obj.read()
                   data_id, proteome, species, codon_use, pep_len, overlap, email = data.strip().split('\t')
                   pep_len = int(pep_len)
                   overlap = int(overlap)
                   
                   make_rc_fragments(data_id, proteome, species, codon_use, pep_len, overlap, RESULT_DIR)                   
                   
                   email_text = f'Subject: Peptide Fragment Generator Job\n\nPeptide Fragment Generator job {data_id} is now complete.\n\nAmino acid and nucleotide FASTA fragment sequence files are available at the web site.'
                   
                   server = smtplib.SMTP(SMTP_SERVER)
                   server.set_debuglevel(1)
                   server.sendmail(FROM_ADDR, email, email_text)
                   server.quit()

                   
        sleep(wait_interval)
    
 
if __name__ == '__main__':
    
    start_agent()
