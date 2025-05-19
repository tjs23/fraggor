import os
from  urllib import request

PROTEOME_URL = 'https://rest.uniprot.org/proteomes/stream?fields=upid%2Corganism%2Corganism_id%2Clineage%2Cprotein_count%2Cbusco&format=tsv&query=(taxonomy_name%3A{})%20AND%20(proteome_type%3A1)'
FASTA_URL = 'https://rest.uniprot.org/uniprotkb/stream?query=(proteome:{})&format=fasta'
PROTEOME_INFO_URL = 'https://rest.uniprot.org/proteomes/stream?fields=upid%2Corganism%2Corganism_id%2Clineage%2Cprotein_count%2Cbusco&format=tsv&query={}'

def get_proteome_info(uid, url=PROTEOME_INFO_URL):
    
    info = None
    furl = url.format(uid)
    
    with request.urlopen(request.Request(furl)) as f:
       lines = f.read().decode('utf-8').split('\n')
       
       for line in lines[1:]: 
           if not line:
               continue
 
           upid, species, tax_id, tax_lineage, count, busco = line.split('\t')
           
           if busco.strip():
               completeness = float(busco[busco.index('C:')+2:busco.index('%[')])
               info = (upid, species, tax_id, tax_lineage, int(count), completeness)
           
           break    
 
    return info
   

def get_uniprot_clade_proteome_info(tax_clade, top=10, verbose=True, url=PROTEOME_URL):
    
    tax_clade = tax_clade.strip().replace(' ', '%20')
    
    furl = url.format(tax_clade)

    if verbose:
        print(f'Proteome query {furl}')

    with request.urlopen(request.Request(furl)) as f:
       lines = f.read().decode('utf-8').split('\n')
    
    proteomes = []
    
    for line in lines[1:]:
        line = line.rstrip('\n')
 
        if not line:
          continue
 
        upid, species, tax_id, tax_lineage, count, busco = line.split('\t')
        
        if busco.strip():
            completeness = float(busco[busco.index('C:')+2:busco.index('%[')])
            proteomes.append([completeness, upid, species, tax_id, tax_lineage, count])
    
    proteomes.sort(reverse=True)
    
    if top:
        proteomes = proteomes[:top]
    
    if verbose:
        for completeness, upid, species, tax_id, tax_lineage, count in proteomes:
            print(f' .. {completeness}% {upid} {species} {tax_id} {count}')
 
    return proteomes
  
  
def download_uniprot_proteome_fasta(species, uid, out_dir='../proteome_data', url=FASTA_URL, overwrite=False, verbose=True):
    
    species = species.split(' (')[0].replace(' ','_')
    species = species.replace('_sp._', '_sp-')
    species = species.replace('_subsp._', '_ss-')
    
    furl = url.format(uid)
    
    if verbose:
        print(f'Query {species}')
        print(f' .. download {furl}')
       
    out_file_path = os.path.join(out_dir, f'{uid}_{species}.fasta')
    
    if overwrite or not os.path.exists(out_file_path):
        if verbose:
            print(f' .. download {furl}')
            
        req = request.Request(furl)
 
        with request.urlopen(req) as f:
            response = f.read()
 
        lines = response.decode('utf-8')

        if verbose:
            print(f' .. obtained {lines.count(">"):,} sequences')
 
        with open(out_file_path, 'w') as file_obj:
            file_obj.write(lines)

        if verbose:
            print(f' .. saved {out_file_path} ')
    
    elif verbose:
        print(f' .. found existing {out_file_path}')
        
    return out_file_path
    

if __name__ == '__main__':
  
    proteomes = []
    #proteomes += get_uniprot_clade_proteome_info('Primates', top=12)
    #proteomes += get_uniprot_clade_proteome_info('Scandentia')
    #proteomes += get_uniprot_clade_proteome_info('Dermoptera')
    #proteomes += get_uniprot_clade_proteome_info('Glires')
    proteomes += get_uniprot_clade_proteome_info('Staphylococcus aureus')
 
    for completeness, upid, species, tax_id, tax_lineage, count in proteomes:
        download_uniprot_proteome_fasta(species, upid)
