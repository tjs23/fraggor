import os, sys
import numpy as np
from glob import glob
from random import randint

import fasta
from matplotlib import pyplot as plt

STEMP_PATH = "/home/tjs23/ext_gh/StemP/Python/"

sys.path.append(STEMP_PATH)

ECOLI_RANKED_CODONS = {'*': [(0.61, 'UAA'), (0.3, 'UGA'), (0.09, 'UAG')],
                       'A': [(0.33, 'GCG'), (0.26, 'GCC'), (0.23, 'GCA'), (0.18, 'GCU')],
                       'C': [(0.54, 'UGC'), (0.46, 'UGU')],
                       'D': [(0.63, 'GAU'), (0.37, 'GAC')],
                       'E': [(0.68, 'GAA'), (0.32, 'GAG')],
                       'F': [(0.58, 'UUU'), (0.42, 'UUC')],
                       'G': [(0.37, 'GGC'), (0.35, 'GGU'), (0.15, 'GGG'), (0.13, 'GGA')],
                       'H': [(0.57, 'CAU'), (0.43, 'CAC')],
                       'I': [(0.49, 'AUU'), (0.39, 'AUC'), (0.11, 'AUA')],
                       'K': [(0.74, 'AAA'), (0.26, 'AAG')],
                       'L': [(0.47, 'CUG'), (0.14, 'UUA'), (0.13, 'UUG'), (0.12, 'CUU'), (0.1, 'CUC'), (0.04, 'CUA')],
                       'M': [(1.0,  'AUG')],
                       'N': [(0.51, 'AAC'), (0.49, 'AAU')],
                       'P': [(0.49, 'CCG'), (0.2, 'CCA'), (0.18, 'CCU'), (0.13, 'CCC')],
                       'Q': [(0.66, 'CAG'), (0.34, 'CAA')],
                       'R': [(0.36, 'CGU'), (0.36, 'CGC'), (0.11, 'CGG'), (0.07, 'CGA'), (0.07, 'AGA'), (0.04, 'AGG')],
                       'S': [(0.25, 'AGC'), (0.17, 'UCU'), (0.16, 'AGU'), (0.15, 'UCC'), (0.14, 'UCG'), (0.14, 'UCA')],
                       'T': [(0.4,  'ACC'), (0.25, 'ACG'), (0.19, 'ACU'), (0.17, 'ACA')],
                       'V': [(0.35, 'GUG'), (0.28, 'GUU'), (0.2, 'GUC'), (0.17, 'GUA')],
                       'W': [(1.0,  'UGG')],
                       'Y': [(0.59, 'UAU'), (0.41, 'UAC')],
                       }
 
CODON_DICTS = {'ecoli_standard':ECOLI_RANKED_CODONS}


from utils.helpers import get_top_alignments, compute_energy
from spectrum_graph import Spectrum_Graph

#TRANSTAB = str.maketrans('{}[]()','******')
 
def stemP_pred(rna_seq, seq_type='short RNA', para={'l':3, 'sl1':0.0, 'sl2':20.0,'p':False,'w':False,'uu':False,}):
    
    graph = Spectrum_Graph()
    graph.find_stems(rna_seq, seq_type, para)
    graph.add_vertices()
    graph.find_edge(para['p'], False)
    graph.build_cliques()

    # compute energy for each clique
    energies, best_idx = compute_energy(graph.cliques, graph.possible_vertex_set)

    if len(energies):
        top_alignments = get_top_alignments(len(rna_seq), best_idx,  graph.possible_vertex_set,  graph.cliques)

    else:
        energies = [0.0]
        top_alignments = [""]

    return sorted(energies, reverse=True), top_alignments[0]


def aa_to_rna(aa_seq, codon_dict=ECOLI_RANKED_CODONS, rank=0):
    
    rna_seq = ''.join([codon_dict[aa][rank][1] for aa in aa_seq])
    
    return rna_seq


def aa_to_rna_rand_codon(aa_seq, codon_dict=ECOLI_RANKED_CODONS, n_gen=100, specific_sites=None, rmax=1):
    
    rna_seqs = []
    n_aa = len(aa_seq)
    ranks_null = [0] * n_aa
    if not specific_sites:
       specific_sites = range(n_aa)
    
    for i in range(n_gen):
        ranks = ranks_null[:]
        for j in specific_sites:
            aa = aa_seq[j]
            m = len(codon_dict[aa])
 
            if m > 1:
                ranks[j] = randint(0, min(m-1, rmax))
        
        rna_seq = ''.join([codon_dict[aa][ranks[j]][1] for j, aa in enumerate(aa_seq)])        
        rna_seqs.append(rna_seq)
        
    return rna_seqs


def aa_to_opt_rna(aa_seq, codon_dict=ECOLI_RANKED_CODONS, n_gen=25, target=4):
    
    def get_max_run(align):
       longest_run = 0
       run = 0

       for char in align:
          if char == '.':
             if run > longest_run:
                longest_run = run
             run = 0
             
          else:
             run += 1
             
       if run > longest_run:
          longest_run = run
       
       return longest_run
    
    rna_seq = aa_to_rna(aa_seq, codon_dict)
    energies, opt_align = stemP_pred(rna_seq)
    
    opt_energy = energies[0]
    opt_seq = rna_seq
    
    if opt_energy <= target:
       return opt_seq, opt_energy, opt_align
        
    opt_run = get_max_run(opt_align)
    alt_seqs = aa_to_rna_rand_codon(aa_seq, codon_dict, n_gen)
    
    for i, rna_seq2 in enumerate(alt_seqs):
       energies, top_align = stemP_pred(rna_seq2)
       top_energy = energies[0]
       top_run = get_max_run(top_align) # Tie break shortest run
       
       if top_energy <= opt_energy: 
           if (top_run < opt_run) or (top_energy < opt_energy):
               opt_energy = top_energy
               opt_seq = rna_seq2
               opt_align = top_align
               
               if opt_energy <= target:                 
                   break
    
    return opt_seq, opt_energy, opt_align
           

def get_random_coil_frags(proteme_ss_path, out_dir, path_prefix='TEST', pep_len=12, overlap=4, codon_use='ecoli_standard', verbose=True):
    
    codon_dict = CODON_DICTS[codon_use]
    
    path_root =  os.path.join(out_dir, f'RCFrags_{path_prefix}_L{pep_len}_O{overlap}_C{codon_use}')
    
    out_aa_fasta = path_root + '.fasta'
    out_nuc_fasta = path_root + '.fna'
    out_nuc_opt_fasta = path_root + '_opt.fna'
    
    named_seqs_aa = []
    named_seqs_rna = []
    named_seqs_rna_opt = []
    
    regions = []
    sl_energ = []
    sl_energ_opt = []
    
    with open(proteme_ss_path) as ss_file_obj:        
        for line in ss_file_obj:
        
            pid, start, seq, ss = line.split()
            start = int(start)
            
            region_start = None
            region_seq = []

            for i, (res_olc, res_ss) in enumerate(zip(seq, ss)):
                res_num = i + start
 
                if res_ss == 'C':
                    if region_start:
                        region_seq.append(res_olc)
 
                    else:
                        region_start = res_num
                        region_seq = [res_olc]
 
                elif region_start:
                    if len(region_seq) >= pep_len:
                        regions.append((region_start, ''.join(region_seq)))
 
                    region_start = None
                    region_seq = []
    
            if region_start and (len(region_seq) >= pep_len):
                regions.append((region_start, ''.join(region_seq)))
        
        frags_aa = []
        frags_rna = []
        frags_rna_opt = []
        
        for region_start, region_seq in regions:
            n = len(region_seq)
            
            for i in range(0, n-pep_len+overlap, overlap):
                j = i + pep_len
                
                if j > n:
                    if (j-n) < (overlap//2):
                        j = n
                        i = j - pep_len
                        
                    else:
                        break
                
                aa_seq = region_seq[i:j]
                if 'X' in aa_seq:
                    continue
                
                start = region_start + i
                end = region_start + j - i
                
                head = f'{pid}:{start}-{end}'
                 
                """
                Check for loop with stemp
                + Look at energy distribution
                + Get top prediction and energy, if over threshold
                + For aligned positions randomly sample N 1st/2nd freq codings
                + Sort, reasses, choose best if better energy
                """
                
                rna_seq = aa_to_rna(aa_seq, codon_dict)
                energies, top_align = stemP_pred(rna_seq)
                sl_energ.append(energies[0])
                               
                opt_seq, opt_energy, opt_align = aa_to_opt_rna(aa_seq, codon_dict)
                sl_energ_opt.append(opt_energy)             
               
                frags_aa.append((head, aa_seq))
                frags_rna.append((head, rna_seq))
                frags_rna_opt.append((head, opt_seq))
        
        named_seqs_aa += frags_aa
        named_seqs_rna += frags_rna
        named_seqs_rna_opt += frags_rna_opt
    
    if verbose:
        fig, ax = plt.subplots()
 
        n = max(max(sl_energ), max(sl_energ_opt))+1
 
        hist, edges = np.histogram(sl_energ, bins=n, range=(0,n))
        ax.plot(edges[:-1], hist, color='#FF0000', label='Initial', alpha=0.5)

        hist, edges = np.histogram(sl_energ_opt, bins=n, range=(0,n))
        ax.plot(edges[:-1], hist, color='#0080FF', label='Optimised', alpha=0.5)
 
        ax.set_ylabel('Count')
        ax.set_xlabel('Loop pair energy')
 
        ax.legend()
 
        plt.show()
    
    fasta.write_fasta(out_aa_fasta, named_seqs_aa)
    if verbose:       
        print(f'Wrote {out_aa_fasta}')

    fasta.write_fasta(out_nuc_fasta, named_seqs_rna)
    if verbose:       
        print(f'Wrote {out_nuc_fasta}')

    fasta.write_fasta(out_nuc_opt_fasta, named_seqs_rna_opt)
    if verbose:       
        print(f'Wrote {out_nuc_opt_fasta}')
    
    return path_root
    
    
if __name__ == '__main__': 
    
    data_dir = '../sec_struc_data/UP000008816_Staphylococcus_aureus/'
    out_dir = '../fragment_data/'
 
    get_random_coil_frags(data_dir, out_dir)
