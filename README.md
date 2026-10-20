# Prosopographical Network Analysis of the Archive of Nūr-Šamaš

This repository accompanies the following publication:

Gonçalves, Carlos. 2027. “Name Disambiguation and Horizons of Possibilities in the Old Babylonian Archive of Nūr-Šamaš.” In *Method and Theory in Archival Studies: Cases from Ancient Western Asia and North Africa*, edited by Carlos Gonçalves and Marcelo Rede. Eisenbrauns. ISBN 978-1-64602-421-6.

---

## Overview

This repository contains a suite of four Python scripts designed to extract and process **prosopographical information** from a set of Old Babylonian documents known as the *archive of Nūr-Šamaš*. The goal is to disambiguate personal names and construct a social network that helps analyze historical relationships through computational methods.

The project combines structured text parsing, manual disambiguation procedures, graph modeling, and network partitioning (using the Louvain algorithm). It was developed for historical analysis and is also intended as a contribution to the digital humanities and Assyriology.

---

## Scripts

The scripts should be run sequentially, as each builds on the output of the previous one:

1. **`01_Parsing.py`**  
   Parses transliterated loan contracts to extract occurrences of marked-up personal names and associated metadata such as role (creditor, debtor, or witness), commodities, and quantities.

2. **`02_Normalizing.py`**  
   Normalizes name forms by converting them from transliterated to readable format (e.g., `nu-ur2-utu` → `Nūr-Šamaš`) and applies optional manual disambiguation from a user-supplied file.

3. **`03_Main_Graph.py`**  
   Builds a graph from co-occurrence data and partitions it using the Louvain modularity algorithm. Nodes represent individuals or name forms, and edges represent co-occurrence in the same document.

4. **`04_Roster.py`**  
   Produces an alphabetically ordered roster of identified persons or name forms, their modularity class, and co-occurrence classes. It also consolidates multiple identifications when specified.

Each script includes detailed inline documentation at the top, describing its function, input and output files, and assumptions.

---

## How to Use

To run the project:

1. Create a project directory on your machine with the following subfolders:
   - `Python_Notebooks`
   - `Processing_Input`
   - `Processing_Output`

2. Place the four Python scripts in `Python_Notebooks`.

3. Place the relevant input files in `Processing_Input`. The required filenames and formats are described in the headers of the individual scripts. Some intermediate files will be generated in `Processing_Output` and used by subsequent scripts.

4. Check the date variables near the beginning of each script (such as `run_date`, `run_date_in`, `run_date_out`, `names_date`, and `disambiguation_statements_date`). Their values must correspond to the filenames of the relevant input and output files.

5. From the `Python_Notebooks` directory, run the scripts sequentially:

   ```bash
   python 01_Parsing.py
   python 02_Normalizing.py
   python 03_Main_Graph.py
   python 04_Roster.py
   ```

The scripts use relative paths, with `base_folder = ".."`, and therefore expect the directory structure described above.

---

## Funding and Acknowledgments

This research was developed as part of a project funded by the **São Paulo Research Foundation (FAPESP)**, Grant 2021/01363-6, active from October 1, 2021, to September 30, 2023. Initial development of the scripts began in 2016 during a fellowship at the **Paris Institute for Advanced Study (2016–2017)**.

---

## Related Publications

Earlier versions of these scripts were used in the following publications:

- Gonçalves, Carlos. “Social Network Analysis and Kinship in the Old Babylonian Diyala: Fathers and Sons in the Archive of Nūr-Šamaš.”  
  *Revista Humanidades Digitais* 15 (2021): 1–9. https://doi.org/10.21814/h2d.3470.

- ———. “Social Network Analysis, Homonyms, and Aliases in the Old Babylonian Diyala: A Study of the Archive of Nūr-Šamaš.”  
  In *Interdisciplinary Research on the Bronze Age Diyala: Proceedings of the Conference Held at the Paris Institute for Advanced Study, 25–26 June*, edited by Carlos Gonçalves and Cécile Michel, 83–101. Subartu 47. Turnhout: Brepols, 2021.

- ———. “The Strength of Witness Ties: A Study of an Old Babylonian Community.”  
  In *Ūmī Annūti Lûḫsusamma Ana Dāriš Aj Amši: “Voglio Pensare a Questi Giorni, e per Sempre Non Dimenticare!”*  
  Edited by Giovanna Matini et al. Writeup, 2023.

Also see the earlier version of this project: [https://github.com/tup-sar/sna-mesopotamia](https://github.com/tup-sar/sna-mesopotamia)

---

## License

The Python scripts in this repository are distributed under the BSD 3-Clause License. See the [LICENSE](LICENSE) file for the full terms.

Users are free to use, modify, and redistribute the scripts under the conditions of this license. In particular, neither the author's name nor the names of contributors may be used to endorse or promote derivative software without prior written permission.

For scholarly use of these scripts, or adaptations substantially based on them, users are requested to cite the associated publication listed above. Independent implementations inspired by the general methods do not require citation of the software, although scholarly acknowledgment is appreciated.
