#!/usr/bin/env python
# coding: utf-8

# In[21]:


# Developed by Carlos Gonçalves, with funding from the São Paulo Research Foundation (FAPESP), Grant 2021/01363-6
# See README for more information
# Version dated May 26, 2025

# This is the fourth of four scripts: 04_Roster

# This script produces an alphabetically ordered list of name forms mentioned in the documentation. 
# For each name form, it indicates the modularity class to which the person belongs and the classes to which 
# that person is connected.

# The script then details each occurrence of the name form in the archive. 
# If the file disambiguation_statements_<disambiguation_date>.txt is not empty, then the 
# occurrences may reflect identifications that have been manually unified by a human analyst.
# The file disambiguation_statements_<disambiguation_date>.txt is manually produced by a human  
# analyst through an iterative process involving analysis of the graph from 03_Main_Graph and review 
# of the output from 04_Roster. Ambiguities are resolved based on this review and recorded in 
# disambiguation_statements_<disambiguation_date>.txt.

# Input files:
# ../Processing_Input/names_<names_date>.txt
# ../Processing_Output/subcomunidades_<run_date>.txt
# ../Processing_Output/parsing_<run_date_out>.txt
# ../Processing_Output/main_graph_<run_date_out>.gexf
# ../Processing_Input/disambiguation_statements_<disambiguation_date>.txt.

# Output file:
# ../Processing_Output/roster_<run_date>.txt


run_date = '_2025_05_26'
names_date = '_2024_02_06'
disambiguation_statements_date = '_2025_05_26'

base_folder = ".."

import io
import re
import networkx as nx
import pandas as pd
from collections import deque
from collections import Counter
# carregando as comunidades a que as pessoas pertencem
# (nomes normalizados, levando em conta profissões e parentes)
h = io.open(base_folder+"/Processing_Output/subcomunidades"+run_date+".txt","r", encoding = "utf-8")
subcomunidade = {}
subcom_maxima = 0
for line in h:
#    line = re.sub(r'[_][0-9]*','',line)
#    line = re.sub(r'[,].*','',line)
    linha_quebrada = line.split('|')
    subcomunidade[linha_quebrada[1].replace('\n','')] = linha_quebrada[0]
    if (subcom_maxima < int(linha_quebrada[0])):
        subcom_maxima = int(linha_quebrada[0])
h.close()
#print ("Comunidades carregadas.")
#print(subcom_maxima,subcomunidade)


# É preciso em seguida criar uma lista alfabética de pessoas (que serão as pessoas do diretório)
lista_de_pessoas = []
for item in subcomunidade.keys():
    lista_de_pessoas.append(item)
lista_de_pessoas = sorted(list(set(lista_de_pessoas)))
#print("Lista de pessoas criada.")
#print(lista_de_pessoas)

# The following creates an alternative listing of persons, ordering by cluster and, secondarily, alphabetically
#lista_de_pessoas = []
#for n_subcom in range(subcom_maxima):
#    
#lista_de_pessoas.append(item)
#lista_de_pessoas = sorted(list(set(lista_de_pessoas)))
#print("Lista de pessoas criada.")
#print(lista_de_pessoas)

# here are the docs that contain dates; I want them to be rendered squared
dated_docs = ["001","002","003","004","005","006","012","013","014","021","022","023","024","025","026","027","028","029","030","031","032","033","034","035","036","037","038","075","115","120","124"]
date_formulae = ['h','f','ah','z','m','d','g','z','ae','y','w','w','r','r','i','w','w','w','x','v','ka','kb','a','ad','aa','e','u','ab','q','p','+s']
datas = {}
for i in range(0,len(dated_docs)):
    datas[dated_docs[i]] = date_formulae[i]
#print (datas)
years_in_subcommunities = ["","","","","","","","","","","","","","","","","","","","",""]


# fazendo um glossário de nomes e nomes normalizados, junto com
# um dicionário de anotações aos nomes
f = io.open(base_folder+"/Processing_Input/names"+names_date+".txt",'r', encoding = "utf-8")
glossario = {}
anotacoes_aos_nomes = {}
for line in f:
    linha_quebrada = line.split('\t')
    if(linha_quebrada[1] != ''):
        anotacoes_aos_nomes[linha_quebrada[1]] = ''
        glossario[linha_quebrada[2]] = linha_quebrada[1]
    else:
        glossario[linha_quebrada[2]] = linha_quebrada[1]
    if ("Unknown" in glossario[linha_quebrada[2]]):
        #print(glossario[linha_quebrada[2]], linha_quebrada[2])
        glossario[linha_quebrada[2]] = glossario[linha_quebrada[2]]+"("+linha_quebrada[2]+")"
    if(linha_quebrada[0] != linha_quebrada[1]):
        if(linha_quebrada[0] == '('+linha_quebrada[1]+')'):
            anotacoes_aos_nomes[linha_quebrada[1]] = "Spelling still to be verified: "+linha_quebrada[0]+'\n'
        #else:
        #    anotacoes_aos_nomes[linha_quebrada[1]] = "Reschid gives a different spelling: "+linha_quebrada[0]+'\n'
    if(linha_quebrada[3].strip() != ''):
        anotacoes_aos_nomes[linha_quebrada[1]] = anotacoes_aos_nomes[linha_quebrada[1]]+linha_quebrada[3]
f.close()
#print("Dicionário de normalizações de nomes carregado.")

# carregando o arquivo geral na memória
e = io.open(base_folder+"/Processing_Output/parsing"+run_date+".txt","r", encoding = "utf-8")
arquivo_geral = []
for line in e:
    linha_quebrada = line.split("|&")
    arquivo_geral.append(linha_quebrada)
e.close()
#print("Arquivo geral carregado.")


# loading identities into memory
i = io.open(base_folder+"/Processing_Input/disambiguation_statements"+disambiguation_statements_date+".txt","r", encoding = "utf-8")
replacements = {}
for line in i:
    if (line[0] == "#"):
        continue
    if ("@end" in line):
        break
    line = line.strip()
    print(line)
    linha_quebrada = line.split('|')
    replacements[linha_quebrada[0],linha_quebrada[1],linha_quebrada[2]] = [linha_quebrada[3],linha_quebrada[4],linha_quebrada[5],linha_quebrada[6]]
i.close()
#print("Identities loaded.")
#print(replacements)


# Aqui começa o processamento. 
# Devemos percorrer toda a lista de nomes normalizados
d = io.open(base_folder+"/Processing_Output/roster"+run_date+".txt","w", encoding = "utf-8")
t = io.open(base_folder+"/Processing_Output/aliases"+run_date+".txt","w", encoding = "utf-8")
G = nx.Graph()
G = nx.read_gexf(base_folder+"/Processing_Output/main_graph"+run_date+".gexf")
frequency_of_conneced_clusters = []

for no in G.nodes():
    G.nodes[no]['Maybe_Parent'] = 0
for item in lista_de_pessoas:
    if (1==1): #item in subcomunidade.keys()): hahaha essa condição não é necessária
        if(True): #subcomunidade[item] == '0' and 'son of' in item):
            #print('\n'+item+'\n'+'Sub-community '+subcomunidade[item]+'.')
            guarda_subcomunidade = '\n'+item+'\n'+'Placed in cluster '+subcomunidade[item]+'.'
            if("son of" in item):
                item_quebrado = item.split(" ")
                papai = item_quebrado[len(item_quebrado)-1]
                for possivel_pai in subcomunidade.keys():
                    if(papai in (possivel_pai.split(" "))[0]):
                        guarda_possible_parent = "Possible parent: "+str(possivel_pai)+", in cluster(s) "+str(subcomunidade[possivel_pai])+"."
                        G.nodes[possivel_pai]['Maybe_Parent'] = G.nodes[possivel_pai]['Maybe_Parent'] + 1
            else:
                guarda_possible_parent = ""
            #d.write('\n'+item+' Sub-community: '+subcomunidade[item]+'\n'+'.')
    else:
        #print('\n'+item)
        d.write('\n'+item+'\n')
    if item in anotacoes_aos_nomes.keys():
        if (anotacoes_aos_nomes[item] != ''):
            #print((anotacoes_aos_nomes[item]).replace("\n",""))
            d.write(anotacoes_aos_nomes[item]+'\n')
    numero_de_ocorrencias = 0
    conjunto = set()
    conjunto_doc_subc = set()
    #print(frequency_of_conneced_clusters)
    if (item in G.nodes()):
        for i in nx.all_neighbors(G,item):
            if (i in subcomunidade.keys() and 'Nūr-Šamaš son of Kūbiya' != i):        
                conjunto = conjunto | {int(subcomunidade[i])}
                list_of_docs = G.edges[item,i]['label'].split(', ')
                for element in list_of_docs:
                    element = element.zfill(3)
                    conjunto_doc_subc = conjunto_doc_subc | {(element,subcomunidade[i])}
        frequency_of_conneced_clusters.append(len(conjunto))
        to_clusters_1 = list(sorted(conjunto))
        to_clusters_1 = [str(x) for x in (to_clusters_1)]
        to_clusters_1 = ' '.join(to_clusters_1).replace(' ',', ')
        #print(guarda_subcomunidade, "Connects to clusters "+to_clusters_1+".")
        d.write(guarda_subcomunidade+" Connects to clusters "+to_clusters_1+".\n")
        if (guarda_possible_parent !=""):
            #print(guarda_possible_parent)
            guarda_possible_parent = ""
        #print("Connections via Documents")
        #print ("Documents     Subcommunities")        
        #for element in sorted(conjunto_doc_subc):
        #    print(element[0]+"            "+element[1])
# here comes the most important part of the directory. We check for all occorências transliterations in 
# arquivo_geral that correspond to the item in lista_de_pessoas being processed at this moment
# The ocorrências must be built from name, kinship, relative and profession (if it all exist), producing the
# termos de comparação
    for ocorrencia in arquivo_geral:  
# The first thing to do is to verify whether ocorrencia in the arquivo_geral 
# corresponds to a homonym or an alias. If this is the case, the present item will have to be compared with the 
# replacement of ocorrencia in the dicionary of replacement. If that is not the case, the present item
# will be compared with the ocorrencia in arquivo geral
#
# Thus, in order to veryfy if this is the case, 
# we must check whether ocorrencia is listed in the dictionary of replacements
        nominho = (ocorrencia[0], ocorrencia[5], ocorrencia[6]+ocorrencia[7])
        if (nominho in replacements.keys()):
            replacement_case = True
        else:
            replacement_case = False
# Now, suppose that in fact the present ocorrencia is in the dicionary of replacements. It needs therefore to
# be replaced
        if(replacement_case == True):            
            replacing_name = replacements[nominho]
            termo_de_comparacao = replacing_name[0]
            para_imprimir = glossario[ocorrencia[0]]+" ("+ocorrencia[0]+")"
            if(replacing_name[1] !=''):  # so, there is a kinship and a relative 
                termo_de_comparacao = termo_de_comparacao + " " +replacing_name[1] + " " + replacing_name[2]
                if(ocorrencia[1] != ''):
                    para_imprimir = para_imprimir+" "+ocorrencia[1]+ " " + glossario[ocorrencia[2]]+" ("+ocorrencia[2]+")"
            if(replacing_name[3] !=''): # so, there is a profession
                termo_de_comparacao = termo_de_comparacao + ", " + replacing_name[3]
                if(ocorrencia[3] != ''):
                    para_imprimir = para_imprimir+", "+ocorrencia[3]
        else:  # that is to say, if replacement_case is False
            termo_de_comparacao = glossario[ocorrencia[0]]
            if ("Unknown" in termo_de_comparacao):
                termo_de_comparacao = termo_de_comparacao+"("+ocorrencia[0]+")"
            para_imprimir = glossario[ocorrencia[0]]+" ("+ocorrencia[0]+")"
            if(ocorrencia[1] != ''):
                termo_de_comparacao = termo_de_comparacao+" "+ocorrencia[1]+ " " + glossario[ocorrencia[2]]
                para_imprimir = para_imprimir+" "+ocorrencia[1]+ " " + glossario[ocorrencia[2]]+" ("+ocorrencia[2]+")"
            if(ocorrencia[3] != ''):
                termo_de_comparacao = termo_de_comparacao+", "+ocorrencia[3]
                para_imprimir = para_imprimir+", "+ocorrencia[3]

# once the termo_de_comparacao is built, we can finally check whether it is the item being 
# analysed at this iteration
        lista_comunidades_do_doc = ""
        if(item == termo_de_comparacao):
            #print(item)
            for element in sorted(conjunto_doc_subc):
                if ocorrencia [5] in element[0]:
                    lista_comunidades_do_doc = lista_comunidades_do_doc+" "+element[1]
            #print(lista_comunidades_do_doc)
            lista_comunidades_do_doc = (lista_comunidades_do_doc.lstrip()).split(' ')
            to_clusters = [int(x) for x in lista_comunidades_do_doc if x !='']
            to_clusters = [str(x) for x in sorted(to_clusters)]
            to_clusters = ' '.join(to_clusters).replace(' ',', ')
            if (ocorrencia[4] == "L"):
                ocorrencia[4] = "creditor"
            if (ocorrencia[4] == "B"):
                ocorrencia[4] = "debtor"
            if (ocorrencia[4] == "W"):
                ocorrencia[4] = "witness"
            
            if (ocorrencia[5] in datas.keys()):
                #print(para_imprimir+", "+ocorrencia[4]+", "+ocorrencia[5]+", "+ocorrencia[6]+ocorrencia[7]+", to cluster(s) "+to_clusters+". Year name:"+datas[ocorrencia[5]])
                d.write(para_imprimir+", "+ocorrencia[4]+", "+ocorrencia[5]+", "+ocorrencia[6]+ocorrencia[7]+", to cluster(s) "+to_clusters+". Year name: "+datas[ocorrencia[5]]+"\n")
                if (years_in_subcommunities[int(subcomunidade[item])] == ""):
                    years_in_subcommunities[int(subcomunidade[item])] = datas[ocorrencia[5]]+ocorrencia[5]
                else:
                    if(datas[ocorrencia[5]]+ocorrencia[5] not in years_in_subcommunities[int(subcomunidade[item])]):
                        years_in_subcommunities[int(subcomunidade[item])] = years_in_subcommunities[int(subcomunidade[item])]+" ,"+datas[ocorrencia[5]]+ocorrencia[5]
                        
            else:
                #print(para_imprimir+", "+ocorrencia[4]+", "+ocorrencia[5]+", "+ocorrencia[6]+ocorrencia[7]+", to cluster(s) "+to_clusters)
                d.write(para_imprimir+", "+ocorrencia[4]+", "+ocorrencia[5]+", "+ocorrencia[6]+ocorrencia[7]+", to cluster(s) "+to_clusters+"\n")
            numero_de_ocorrencias = numero_de_ocorrencias + 1
    t.write(item+"|"+subcomunidade[item]+"|"+(", ".join(str(sorted(conjunto))))+"|"+str(numero_de_ocorrencias)+"\n")
print(Counter(frequency_of_conneced_clusters))
d.close()
t.close()
nx.write_graphml(G,base_folder+"/Processing_Output/main_graph"+run_date+".graphml")
nx.write_gexf(G,base_folder+"/Processing_Output/main_graph"+run_date+".gexf")
print("Total de clusters:",1+ subcom_maxima)
for i in range(len(years_in_subcommunities)):
    print("Subcommunity "+str(i)+": "+years_in_subcommunities[i])


# In[ ]:





# In[ ]:




