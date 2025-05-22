# Fraggor - Random Coil Fragment Peptide Generator

This was conceived and created by Dom Bellini and Tim Stevens.

Fraggor generates datasets of naturally occurring peptides that are likely random-coil,
(i.e. largely unstructured) which may be used in investigations of peptide binding etc.
Accordingly, Fraggor not only generates peptide amino acid sequences, but also nucleic acid sequences for creating expression libraries.

The Flask web app provides a service to calculate peptide datasets and archive the data to give a continually
expanding resource of pre-computed results.

The overall workflow of the Fraggor system is roughly as follows:
 
* Whole proteomes are obtained from UniProt via taxonomic selection
* Protein sequences are scanned for regions of likely random-coil secondary structure using S4PRED
* Regions of random-coil with an amino acid sequence exceeding a minimum length (the fragment size) are extracted
* Selected regions are split into overlapping fragments of specified length; stepping an "offset" number of positions through the sequence, and always including a fragment that covers the region's end.
* Peptide fragment amino acid sequences are converted into nucleic acid sequences using a specific codon set
* Nucleic acid sequences are generated using both the most common codon for each amino acid and by optimising the sequence to minimise RNA stem loops
* RNA stem loops are minimised by randomly selecting from among the codons available for each amino acid and evaluating the secondary structure content using StemP
