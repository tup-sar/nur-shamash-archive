#!/usr/bin/env python
# coding: utf-8

# In[26]:


# Developed by Carlos Gonçalves, with funding from the São Paulo Research Foundation (FAPESP), Grant 2021/01363-6
# See README for more information
# Version dated May 26, 2025

# This is the third of four scripts: 03_Main_Graph

# This script uses the output of the previous steps to generate a graph representing the network of name forms 
# in the archive. Each node corresponds to one name form, but as more name forms are disambiguated, the
# the graph increasingly approximated a graph of individuals and their connections. 

# The script partitions the graph using the Louvain algorithm for modularity optimization (as implemented in 
# the NetworkX package). If the file disambiguation_statements_<disambiguation_date>.txt is empty, the 
# resulting partition can serve as a reference by a human analyst to guide the disambiguation process. 
# Once disambiguation decisions are made and recorded in 
# disambiguation_statements_<disambiguation_date>.txt, all scripts must be rerun 
# (parsing, normalizing, and main graph).

# Each node includes metadata such as the person’s preferred commodity, modularity class, and information 
# about the documents in which they appear.

# The resulting graph is written in both GraphML and GEXF formats.

# Input file:
# ../Processing_Output/normalized_names_<run_date_out>.txt

# Output files:
# ../Processing_Output/subcomunidades_<run_date>.txt
# ../Processing_Output/main_graph_<run_date_out>.graphml
# ../Processing_Output/main_graph_<run_date_out>.gexf



run_date = '_2025_05_26'
run_date_out = '_2025_05_26'
names_date = '_2024_02_06'
disambiguation_statements_date = '_2025_05_26'
base_folder = ".."

import networkx as nx
import io
import itertools
import matplotlib.pyplot as plt
import pandas as pd
# This is for modularity
import community
h = io.open(base_folder+"/Processing_Output/normalized_names"+run_date+".txt","r", encoding = "utf-8")
G = nx.Graph()

# declare here the list of documents to be analysed; they are numbered 1 to 157
# 75, 116, 119, 120, 121 are documents of a different nature, so they should not be included in the SNA study
list_of_docs = [i for i in range(1,119) if ((i != 75) & (i != 116))]

# here are the docs that contain dates; I want them to be rendered squared
dated_docs = [1,2,3,4,5,6,12,13,14,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,75,115,120,124]
date_formulae = ['h','f','ah','z','m','d','g','z','ae','y','w','w','r','r','i','w','w','w','x','v','ka','kb','a','ad','aa','e','u','ab','q','p','+s']
datas = {}

cor = []
for i in range(0,len(dated_docs)):
    datas[dated_docs[i]] = date_formulae[i]
counter = 0
names_this_doc = []

# colors for the modularity classes
# this funcion is called after the graph is created and partitioned, and it 
# creates the hexadecimal color codes according to the number of modularity classes
color_dict = {}
def create_colors(set_of_numbers):
    list_of_numbers = list(sorted(set_of_numbers))
    number_of_colors = len(list_of_numbers)
    step = int(255 / number_of_colors)
    n = step
    for number in list_of_numbers:
        base16 = f'{n:0x}'.zfill(2)
        color_code="#"+base16+base16+base16.strip("x")       
        color_dict[number] = color_code
        n = n + step


# this function takes a list of names and 
# creates all the edges linking two of these names
def create_edges(list_of_edges, number_of_doc):
# in some damaged tablets, the name of Nur-Shamash is not readable
# if this is the case, let us add his name
#    print("Vamos criar as arestas do doc. ", number_of_doc)
    if ('Nūr-Šamaš son of Kūbiya' not in list_of_edges):
        list_of_edges.append('Nūr-Šamaš son of Kūbiya')
# But it may also happen that his name is written only 
    set_of_edges = set(list_of_edges)
    pairs_of_edges = set(itertools.combinations(set_of_edges,2))
#    print(pairs_of_edges)
#    G.add_edges_from(pairs_of_edges)
    for aresta in pairs_of_edges:
        if (aresta not in G.edges):
            print(aresta)
            G.add_edge(*aresta)
            G.edges[aresta]['weight'] = 1
            G.edges[aresta]['label'] = str(number_of_doc)
        else:
            G.edges[aresta]['weight'] = G.edges[aresta]['weight'] + 1
            G.edges[aresta]['label'] = G.edges[aresta]['label'] + ', ' + str(number_of_doc)

            
# now we begin!
for line in h:
    #print (line)
    linha_quebrada = line.split('|')
# now it comes the check to verify whether we are in the chosen range of docs.
    if (int(linha_quebrada[5]) not in list_of_docs):
        continue
    if (int(linha_quebrada[5]) in dated_docs):
        numero_lados_dated = 'Rectangle'
        dated_doc = linha_quebrada[5]
    else:
        numero_lados_dated = 'Ellipse'
        dated_doc = ''
# each time material from a new document begins being parsed, a few things happen:
# 1) the edges must be spanned
# 2) the list of the names in this doc (now the previous doc) must be reset
#    it is this list that will be spanned to create new edges for the graph
# 3) counter is updated (to the value of the just accepted document)
    if(counter != int(linha_quebrada[5])):
        if (len(names_this_doc) != 0):
            create_edges(names_this_doc, counter)
        names_this_doc = []
        counter = int(linha_quebrada[5])
# a special case is Nur-Shamash, the lender; the name of this father must always appear    
    if((linha_quebrada[0]== 'Nūr-Šamaš') and (linha_quebrada[4] == 'L')):
        linha_quebrada[1] = 'son of'
        linha_quebrada[2] = 'Kūbiya'
# if a name is accompanied by a father's name, take the father's name into account to create a node
# if a name is accompanied by a owner's name, then we take into account the "slave" satutus of the person
# idem for wife
    if(linha_quebrada[1] == 'son of'):
        novo_no = linha_quebrada[0]+" son of "+linha_quebrada[2]
    elif (linha_quebrada[1] == 'daughter of'):
        novo_no = linha_quebrada[0]+" daughter of "+linha_quebrada[2]
    elif (linha_quebrada[1] == 'slave of'):
        novo_no = linha_quebrada[0]+" slave of "+linha_quebrada[2]
    elif(linha_quebrada[1] == 'wife of'):
        novo_no = linha_quebrada[0]+" wife of "+linha_quebrada[2]
    else:
        novo_no = linha_quebrada[0]
# Let us add profession to the name of the node (if there is one)
# Also, it is useful that profession appears as a separate node attribute and that is the 
# funcion of the variable profession
    if (linha_quebrada[3] != ''):
        novo_no = novo_no + ', ' + linha_quebrada[3]
        profession = linha_quebrada[3]
    else:
        profession = '--'


# is this a new or a repeated node?
    if novo_no not in list(G.nodes):
#        print("New node!!!")
        G.add_node(novo_no)
        G.nodes[novo_no]['grau'] = 1
        G.nodes[novo_no]['profissao'] = profession
        G.nodes[novo_no]['PolygonDated'] = numero_lados_dated
        G.nodes[novo_no]['Dated'] = dated_doc
        G.nodes[novo_no]['Roles'] = linha_quebrada[4]
        G.nodes[novo_no]['Appears'] = int(linha_quebrada[5])
        G.nodes[novo_no]['Disappears'] = int(linha_quebrada[5])

        
        if("B" in linha_quebrada[8]):
            G.nodes[novo_no]['Barley'] = 1
        else:
            G.nodes[novo_no]['Barley'] = 0
        
        if("S" in linha_quebrada[8]):
            G.nodes[novo_no]['Silver'] = 1
        else:
            G.nodes[novo_no]['Silver'] = 0
        
        if("E" in linha_quebrada[8]):
            G.nodes[novo_no]['Emmer'] = 1
        else:
            G.nodes[novo_no]['Emmer'] = 0
            
        if("C" in linha_quebrada[8]):
            G.nodes[novo_no]['Chickpea'] = 1
        else:
            G.nodes[novo_no]['Chickpea'] = 0
        
        G.nodes[novo_no]['ValueBarley'] = float(linha_quebrada[9])
        G.nodes[novo_no]['ValueSilver'] = float(linha_quebrada[10])
        G.nodes[novo_no]['ValueEmmer'] = float(linha_quebrada[11])
        G.nodes[novo_no]['ValueChickpea'] = float(linha_quebrada[12])
         
        
        if (linha_quebrada[4] == 'B'):
            G.nodes[novo_no]['B_ValueBarley'] = float(linha_quebrada[9])
            G.nodes[novo_no]['B_ValueSilver'] = float(linha_quebrada[10])
            G.nodes[novo_no]['B_ValueEmmer'] = float(linha_quebrada[11])
            G.nodes[novo_no]['B_ValueChickpea'] = float(linha_quebrada[12])
        else:
            G.nodes[novo_no]['B_ValueBarley'] = float("0")
            G.nodes[novo_no]['B_ValueSilver'] = float("0")
            G.nodes[novo_no]['B_ValueEmmer'] = float("0")
            G.nodes[novo_no]['B_ValueChickpea'] = float("0")

        if (linha_quebrada[4] == 'W'):
            G.nodes[novo_no]['W_ValueBarley'] = float(linha_quebrada[9])
            G.nodes[novo_no]['W_ValueSilver'] = float(linha_quebrada[10])
            G.nodes[novo_no]['W_ValueEmmer'] = float(linha_quebrada[11])
            G.nodes[novo_no]['W_ValueChickpea'] = float(linha_quebrada[12])
        else:
            G.nodes[novo_no]['W_ValueBarley'] = float("0")
            G.nodes[novo_no]['W_ValueSilver'] = float("0")
            G.nodes[novo_no]['W_ValueEmmer'] = float("0")
            G.nodes[novo_no]['W_ValueChickpea'] = float("0")
        
    else:
#        print("Repeated node...")
        G.nodes[novo_no]['grau'] = G.nodes[novo_no]['grau'] + 1
        G.nodes[novo_no]['Dated'] = G.nodes[novo_no]['Dated']+dated_doc
        if (int(linha_quebrada[5]) < G.nodes[novo_no]['Appears']):
            G.nodes[novo_no]['Appears'] = int(linha_quebrada[5])
        if (int(linha_quebrada[5]) > G.nodes[novo_no]['Disappears']):
            G.nodes[novo_no]['Disappears'] = int(linha_quebrada[5])


        if (G.nodes[novo_no]['PolygonDated'] == 'Ellipse'):
            G.nodes[novo_no]['PolygonDated'] = numero_lados_dated
        if (G.nodes[novo_no]['Roles'] != linha_quebrada[4]):
            G.nodes[novo_no]['Roles'] = 'D'
        
        if("B" in linha_quebrada[8]):
            G.nodes[novo_no]['Barley'] = G.nodes[novo_no]['Barley'] + 1 
       
        if("S" in linha_quebrada[8]):
            G.nodes[novo_no]['Silver'] = G.nodes[novo_no]['Silver'] + 1
        
        if("E" in linha_quebrada[8]):
            G.nodes[novo_no]['Emmer'] = G.nodes[novo_no]['Emmer'] + 1

        if("C" in linha_quebrada[8]):
            G.nodes[novo_no]['Chickpea'] = G.nodes[novo_no]['Chickpea'] + 1

        G.nodes[novo_no]['ValueBarley'] = G.nodes[novo_no]['ValueBarley'] + float(linha_quebrada[9])
        G.nodes[novo_no]['ValueSilver'] = G.nodes[novo_no]['ValueSilver'] + float(linha_quebrada[10])
        G.nodes[novo_no]['ValueEmmer'] = G.nodes[novo_no]['ValueEmmer'] + float(linha_quebrada[11])
        G.nodes[novo_no]['ValueChickpea'] = G.nodes[novo_no]['ValueChickpea'] + float(linha_quebrada[12])
        
        if (linha_quebrada[4] == 'B'):
            G.nodes[novo_no]['B_ValueBarley'] = G.nodes[novo_no]['B_ValueBarley'] + float(linha_quebrada[9])
            G.nodes[novo_no]['B_ValueSilver'] = G.nodes[novo_no]['B_ValueSilver'] + float(linha_quebrada[10])
            G.nodes[novo_no]['B_ValueEmmer'] = G.nodes[novo_no]['B_ValueEmmer'] + float(linha_quebrada[11])
            G.nodes[novo_no]['B_ValueChickpea'] = G.nodes[novo_no]['B_ValueChickpea'] + float(linha_quebrada[12])
        
        if (linha_quebrada[4] == 'W'):
            G.nodes[novo_no]['W_ValueBarley'] = G.nodes[novo_no]['W_ValueBarley'] + float(linha_quebrada[9])
            G.nodes[novo_no]['W_ValueSilver'] = G.nodes[novo_no]['W_ValueSilver'] + float(linha_quebrada[10])
            G.nodes[novo_no]['W_ValueEmmer'] = G.nodes[novo_no]['W_ValueEmmer'] + float(linha_quebrada[11])
            G.nodes[novo_no]['W_ValueChickpea'] = G.nodes[novo_no]['W_ValueChickpea'] + float(linha_quebrada[12])

            
            # now we add the just retrieved name (maybe + son of name) to the list of the names of the present doc
    names_this_doc.append(novo_no)
create_edges(names_this_doc, counter)
h.close()
# Select favourite commodity of each person
for no in G.nodes():
    if (G.nodes[no]['Emmer'] > G.nodes[no]['Barley'] and G.nodes[no]['Emmer'] > G.nodes[no]['Silver']):
        G.nodes[no]['FavouriteCommodity'] = 'E'
    elif (G.nodes[no]['Barley'] > G.nodes[no]['Emmer'] and G.nodes[no]['Barley'] > G.nodes[no]['Silver']):
        G.nodes[no]['FavouriteCommodity'] = 'B'
    elif (G.nodes[no]['Silver'] > G.nodes[no]['Barley'] and G.nodes[no]['Silver'] > G.nodes[no]['Emmer']):
        G.nodes[no]['FavouriteCommodity'] = 'S'
    else:
        G.nodes[no]['FavouriteCommodity'] = 'N'


# Maximise modularity
H = nx.Graph()
H = G.copy()
# Here there are two possibilities: to include 'Nūr-Šamaš son of Kūbiya' in the modularity calculation
#                                   to exclude 'Nūr-Šamaš son of Kūbiya' from it.
# This has to be made manually by changing the variable exclude_nur_shamash
exclude_nur_shamash = False
if (exclude_nur_shamash):
    H.remove_node('Nūr-Šamaš son of Kūbiya')
part = community.best_partition(H, randomize=None, random_state=None)
#mod = community.modularity(part,H)
# let us see how many modularity classes have been created
set_of_class_numbers = set()
for entry in part.keys():
    set_of_class_numbers.add(part[entry])
#print(set_of_class_numbers)

# This segment eliminates randomness in the numbering of classes
total_communities = len(set_of_class_numbers)
name_forms_sorted = sorted(part)
positions_permutation = [-1]*total_communities
count_position = 0
for name_form in name_forms_sorted:
    n = part[name_form]
    if positions_permutation[n] == -1:
        positions_permutation[n] = count_position
        count_position = count_position + 1
print(positions_permutation)

for name_form in part.keys():
    part[name_form] = positions_permutation[part[name_form]]

# we have to create an equal number of colors
create_colors(set_of_class_numbers)
#print(color_dict)

# now we have to include the color code in the graph nodes; there are two cases according to exclusion or not
# of 'Nūr-Šamaš son of Kūbiya'
for no in G.nodes():
    if(no != 'Nūr-Šamaš son of Kūbiya'):
        number = part.get(no)
        G.nodes[no]['Color'] = color_dict[number]
    else:
        if(exclude_nur_shamash):
            G.nodes[no]['Color'] = "#000000"
        else:
            number = part.get(no)
            G.nodes[no]['Color'] = color_dict[number]

# recording data on subcomunities
j = io.open(base_folder+"/Processing_Output/subcomunidades"+run_date+".txt","w", encoding = "utf-8")
for pessoa in G.nodes():
    if(pessoa != 'Nūr-Šamaš son of Kūbiya'):
        j.write(str(part.get(pessoa))+'|'+str(pessoa)+'\n')
        G.nodes[pessoa]['Modularity'] = part.get(pessoa)
    else:
        if(exclude_nur_shamash):
            j.write("-1"+"|"+str(pessoa)+'\n')
            G.nodes[pessoa]['Modularity'] = "-1"
        else:
            j.write(str(part.get(pessoa))+'|'+str(pessoa)+'\n')
            G.nodes[pessoa]['Modularity'] = part.get(pessoa)
j.close()

# Let us introduce a new node attribute, that of connector
# A node is a connector iff it has a neighbour with different colour.
# First step. Add the attribute with value 1
# connector will in fact contain the number of different communities a node keeps relations to
# Now we iterate thoughout all the edges
# For each edge, we look at the nodes and increment it by 1 iff the edge contains nodes from different communities
for no in G.nodes():
    G.nodes[no]['connector'] = 1
    classes_dos_vizinhos = {part.get(no)}
    for vizinho in nx.all_neighbors(G,no):
        if(vizinho != 'Nūr-Šamaš son of Kūbiya'):
            classes_dos_vizinhos = classes_dos_vizinhos | {part.get(vizinho)}
    G.nodes[no]['connector'] = len(classes_dos_vizinhos)
    #print(no, G.node[no]['connector'], classes_dos_vizinhos)

# Agora vamos calcular betweeness centrality
centralidade = set()
centralidade = nx.betweenness_centrality(H)
for no in H.nodes():
#    G.nodes[no]['Centralidade'] = centralidade[no]
    if(no != 'Nūr-Šamaš son of Kūbiya'):
        G.nodes[no]['Centralidade'] = float(centralidade[no])
    else:
        G.nodes[no]['Centralidade'] = float(0)
nx.write_graphml(G,base_folder+"/Processing_Output/main_graph"+run_date_out+".graphml")
nx.write_gexf(G,base_folder+"/Processing_Output/main_graph"+run_date_out+".gexf")

# Here a report that will be useful to compare graphs
print("Numer of subcommunities: ",len(set_of_class_numbers))
dF_nomes = pd.DataFrame((no,G.nodes[no]['Centralidade'],G.nodes[no]['connector'],G.nodes[no]['Roles']) for no in G.nodes())
#dF_nomes = dF_nomes.set_index(0)
dF_nomes.rename(columns={0:'Name', 1:'Betweenness', 2:'Number of Communities', 3:'Roles'}, inplace = True)
print (dF_nomes)
dF_nomes = dF_nomes.sort_values('Betweenness',ascending = False)
d1 = dF_nomes.head(6)
d1 = d1.replace({'Roles': {'D': 'W and B'}})
print (d1)
dF_nomes = dF_nomes.sort_values('Number of Communities',ascending = False)
d2 = dF_nomes.head(20)
d2 = d2.drop([0])
d2 = d2.replace({'Roles': {'D': 'W and B'}})
print (d2)
d3 = pd.merge(d1,d2)
print(d3)


# In[ ]:





# In[ ]:





# In[ ]:




