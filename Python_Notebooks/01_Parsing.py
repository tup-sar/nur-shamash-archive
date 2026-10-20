#!/usr/bin/env python
# coding: utf-8

# In[10]:


# Developed by Carlos Gonçalves, with funding from the São Paulo Research Foundation (FAPESP), Grant 2021/01363-6
# See README for more information
# Version dated May 26, 2025

# This is the first of four scripts: 01_Parsing

# This script retrieves prosopographical information from a file containing transliterations of the documents 
# from the archive of Nūr-Šamaš. The transliteration file is a modified version of one automatically generated 
# by the Cuneiform Digital Library Initiative (CDLI). For use with this script, personal names have been 
# manually marked with asterisks, since the current version of the code cannot identify personal names 
# independently.

# The script parses each loan contract, identifies the marked-up personal names, and determines whether each 
# one appears as a creditor, debtor, or witness. It also records the commodity involved in each contract, 
# along with its quantity.

# Each name occurrence is recorded with the document number, tablet face, line number, and any additional 
# identifying information (such as kinship or profession) found in the text.

# Input file:
# ../Processing_Input/00_cdli_atf_20170317.txt

# Output files:
# ../Processing_Output/parsing_<run_date>_out.txt
# ../Processing_Output/interests_<run_date>_out.txt
# ../Processing_Output/amounts_<run_date>_out.txt


run_date_out = '_2025_05_26'
base_folder = ".."

import io
import re # for regular expressions

# definitions of state variables
atento_num_doc = 0 # waiting for a number of document (1) or relaxed (0)
already_have_doc = 0 # this will be changed to 1 when the first doc is loaded into memory
montando_nome = 0
montando_cadastro = 0
# nome é uma variável de uso, para montar tanto o nome da pessoa como do parente, se houver
nome = ''
# as próximas variáveis compõem um cadastro
# isso quer dizer que às vezes é preciso montar dois nomes para montar um cadastro
pessoa = ''
parentesco = ''
parente = ''
profissao = ''
num_doc = '' 
face_id = ''
line_id = ''
face_comeco_cadastro = ''
linha_comeco_cadastro = ''
commodity_do_doc = set()
estado_amount = 'esperando_amount'
amount_do_doc = ''
converted_amount_do_doc = 0
juro_do_doc = ''
valores_do_doc = [0,0,0,0]

# as variáveis papel servem para marcar o papel de cada pessoa em um contrato, L, B ou W. 
# a primeira indica qual é o papel da pessoa cujo nome está sendo lido
# a segunda indica em que parte do documento estamos
# papel_L_gravado = 0 --> nenhum nome de L foi gravado até agora
# papel_L_gravado = 1 --> foi gravado um nome de L
# papel_L_gravado = 2 --> os nomes de L estão todos gravados (nos contratos de 1 a 199, só a um nome de L)
# Ver a machine correspondente para mais detalhes
papel_atual = 'B'
papel_L_gravado = 0
papel_proximo = ''

# o arquivo geral é uma lista de cadastros do documento sendo processado
arquivo_do_documento = []


# declare here the list of documents to be analysed; they are numbered 1 to 157
# 75, 116, 119, 120, 121 are documents of a different nature, so they should not be included in the SNA study
documentos_a_ler = [i for i in range(1,119) if ((i != 75) & (i != 116))]

# é preciso também criar um dicionário para as palavras em acadiano ou sumério que são importantes
dicio = {}
lista_de_profissoes = ['dub-sar','sipa','aga-us2','gu-za-la2','aszgab','muhaldim','nu-esz3','szitim',
                       'nu-{gesz}kiri6','nar','szagina','ku5-ku5','a-zu','szu-i','ha-za-num2','simug',
                      'ugula-gesz2-da','bahar2','nu-banda3','geme2','di-kud','UD-ASZ2-DI','gu-ga-lim',
                      'dam-gar3','gu-za-la','KU-RU-(x)-x','gu-gal','lu2-nu-hu-um']
traducao_de_profissoes = ['scribe','shepherd','soldier','official','leatherworker','cook','priest','architect',
                         'gardener','musician','governor','cripple','physician','barber','mayor','smith',
                         'supervisor of sixty','potter','overseer','female worker','judge','??(UD-ASZ2-DI)','canal inspector',
                         'merchant','chair-bearer','KU-RU?-(x)-x','canal inspector','from Nuḫum']
for i,j in zip(lista_de_profissoes,traducao_de_profissoes):
    dicio[i] = j

lista_de_parentescos = ['dumu','dumu-munus','dam-a-ni','dam-szu','ARAD','ARAD2','szesz-a-ni']
traducao_de_parentescos = ['son of','daughter of','wife of','wife of','slave of','slave of','brother of']

for i,j in zip(lista_de_parentescos,traducao_de_parentescos):
    dicio[i] = j
#print(dicio)

# Aqui ficam as funções. Ao contrário das máquinas,
# 1) elas não têm estado, ie, independentemente da situação executam a mesma "função""
# 2) não são necessariamente chamadas para todos os tokens
# Entretanto, igualmente às máquinas elas podem às vezes alterar variáveis globais

# Função 1: to clean tokens and names
def limpa(token_local):
    token_limpo = token_local
    for lixo in ['#','_','[',']','{disz}','*','!','?','{d}', '<','>']:
        token_limpo = token_limpo.replace(lixo,'')
    while 'x x' in token_limpo:
        token_limpo = token_limpo.replace('x x','x-x')
    return token_limpo

# Função 2: it reads the number of the document from the list_of_tokens
def le_num_doc():
    global num_doc
    global atento_num_doc
    global token
    for token in list_of_tokens:
        if (re.match(r"[0-9]{3}", token)):
            num_doc = token
            return

# Função 3: updates the position by changing global variables face_id and line_id
def updates_position(token):
    global face_id
    global line_id
    face_id_atual = face_id
    line_id_atual = line_id
    if(token == '@obverse'):
#        if(face_id == 'env.'):
#            face_id = 'obv.env.'
#        else:
        face_id = 'obv.'
        line_id = ''
    if(token == '@reverse'):
#        if(face_id == 'env.'):
#            face_id = 'rev.env.'
#        else:
        face_id = 'rev.'
        line_id = ''
    if (token == '@top'):
        face_id = 'top'
        line_id = ''
    if (token == '@bottom'):
        face_id = 'bottom'
        line_id = ''
    if (token == '@left'):
        face_id = 'left'
        line_id = ''
    if (token.startswith('@seal')):
        face_id = token
    if (token == '@env'):
        face_id = 'env.'
        line_id = ''
    if token.startswith(('1.','2.','3.','4.','5.','6.','7.','8.','9.','10.',
                         '11.','12.','13.','14.','15.','16.','17.','18.','19.','20.',
                        '1a.','2a.','3a.','4a.','5a.','6a.','7a.','8a.','9a.','10a.',
                         '11a.','12a.','13a.','14a.','15a.','16a.','17a.','18a.','19a.','20a.',
                        '1b.','2b.','3b.','4b.','5b.','6b.','7b.','8b.','9b.','10b.',
                        '11b.','12b.','13b.','14b.','15b.','16b.','17b.','18b.','19b.','20b.',
                        '1c.','2c.','3c.','4c.','5c.','6c.','7c.','8c.','9c.','10c.',
                         '11c.','12c.','13c.','14c.','15c.','16c.','17c.','18c.','19c.','20c.',
                        '1\'.','2\'.','3\'.','4\'.','5\'.','6\'.','7\'.','8\'.','9\'.','10\'.',
                         '11\'.','12\'.','13\'.','14\'.','15\'.','16\'.','17\'.','18\'.','19\'.','20\'.',
                        )):
        line_id = token.partition('.')[0]
    
    if((face_id_atual == face_id) and (line_id_atual == line_id)):
        return 1
    else:
        return 0

# Função 4: converte um amount escrito com palavras em um valor numérico
# total de qûm para barley e emmer
# total de uttatum para silver
def converte_amount(amount_passado):
    commodity = ''
    valor = 0
    fila_de_numeros = list()
    amount_passado = amount_passado.replace("("," (")
    amount_quebrado = amount_passado.split(" ")
    #print(amount_quebrado)
    if("ziz2" in amount_passado):
        commodity = "emmer"
    elif ("ku3-babbar" in amount_passado or "gin2" in amount_passado or "ma-na" in amount_passado):
        commodity = "silver"
    elif ("gu2-gal" in amount_passado):
        commodity = "chickpea"
    else:
        commodity = "barley"
    if ("n " in amount_passado):
        commodity = commodity + " 0"
        return commodity
    else:
        if(commodity == "silver"):
            for pedaco in amount_quebrado:
                #print(fila_de_numeros)
                
                if (re.match('^[0-9]+$', pedaco)):
                    numerador = int(pedaco)*60
                    denominador = 60
                    fila_de_numeros.append([numerador,denominador])
                if (pedaco == "(u)"):
                    ultimo_par = fila_de_numeros.pop()
                    ultimo_par[0] = int(ultimo_par[0])*10
                    fila_de_numeros.append(ultimo_par)
                if ("(disz)" in pedaco and len(fila_de_numeros) >= 2):
                    ultimo_par = fila_de_numeros.pop()
                    penultimo_par = fila_de_numeros.pop()
                    ultimo_par[0] = ultimo_par[0] + penultimo_par[0]
                    fila_de_numeros.append(ultimo_par)
                if ("1/3" in pedaco):
                    fila_de_numeros.append([20,60])
                if "gin2" in pedaco:
                    ultimo_par = fila_de_numeros.pop()
                    valor = valor + ultimo_par[0]*180/ultimo_par[1]
                if "ma-na" in pedaco:
                    ultimo_par = fila_de_numeros.pop()
                    valor = valor + ultimo_par[0]*60*180/ultimo_par[1]
            return commodity + " " + str(valor)
        if(commodity in {"barley", "emmer", "chickpea"}):
            for pedaco in amount_quebrado:
                #print(fila_de_numeros)
                
                if (re.match('^[0-9]+$', pedaco)):
                    numerador = int(pedaco)*60
                    denominador = 60
                    fila_de_numeros.append([numerador,denominador])                
                
                if (pedaco == "(u)"):
                    ultimo_par = fila_de_numeros.pop()
                    ultimo_par[0] = int(ultimo_par[0])*10
                    fila_de_numeros.append(ultimo_par)
                
                if (("(disz)" in pedaco or "asz" in pedaco) and len(fila_de_numeros) >= 2):
                    ultimo_par = fila_de_numeros.pop()
                    penultimo_par = fila_de_numeros.pop()
                    ultimo_par[0] = ultimo_par[0] + penultimo_par[0]
                    fila_de_numeros.append(ultimo_par)
                if ("1/3" in pedaco):
                    fila_de_numeros.append([20,60])

                if "gur" in pedaco:
                    ultimo_par = fila_de_numeros.pop()
                    valor = valor + ultimo_par[0]*300/ultimo_par[1]
                if "barig" in pedaco:
                    ultimo_par = fila_de_numeros.pop()
                    valor = valor + ultimo_par[0]*60/ultimo_par[1]
                if "ban2" in pedaco:
                    ultimo_par = fila_de_numeros.pop()
                    valor = valor + ultimo_par[0]*10/ultimo_par[1]
                if "sila3" in pedaco:
                    ultimo_par = fila_de_numeros.pop()
                    valor = valor + ultimo_par[0]/ultimo_par[1]
                #print(valor)
            if(len(fila_de_numeros) != 0):
                ultimo_par = fila_de_numeros.pop()
                valor = valor + ultimo_par[0]
            return commodity + " " + str(valor)
    return

# Now we have to define the machines
# Regras importantes:
# 1) o estado de cada máquina é alterado pela própria máquina
# 2) todas as máquinas recebem todos os tokens (senão elas não podem saber se devem alterar seus estados)
# 3) todas as máquinas podem alterar as váriáveis de cadastro o próprio arquivo_geral 
#  (como uma pilha, o que é prático)
# 4) máquinas não podem avançar nem retroceder a distribuição de tokens

# Machine 3: vai montar nome
# nome e montando_nome são variáveis globais
def vai_montar_nome(token_local,token_limpo_local):
    global nome, montando_nome
    if(montando_nome == 2):
        nome = ''
        montando_nome = 0
    pedacos = token_local.partition('*')
    if(montando_nome == 0 and token_local.count('*') == 2):
        nome = pedacos[2]
        pedacos = nome.partition('*')
        nome = pedacos[0]
        montando_nome = 2
        return
    if(montando_nome == 0 and token_local.count('*') == 1):
        nome = nome + pedacos[2]
        montando_nome = 1
        return 
    if(montando_nome == 1 and token_local.count('*') == 0):
        nome = nome + " " + token_local
        return 
    if(montando_nome == 1 and token_local.count('*') == 1):
        nome = nome + " " + pedacos[0]
        montando_nome = 2
        return
    

# Machine 4: monta cadastro. 
# pessoa e montando_pessoa são variáveis globais

def vai_montar_cadastro(token_local,token_limpo_local):
    global parentesco, profissao, parente, pessoa, montando_cadastro, arquivo_do_documento 
    global papel_atual, papel_L_gravado, commodity_do_doc
    global face_comeco_cadastro, linha_comeco_cadastro
    estado_atual = montando_cadastro
    

    if (montando_nome == 2 and pessoa != "" and montando_cadastro == 2):
        montando_cadastro = 10
    if (montando_nome == 2 and pessoa != "" and montando_cadastro == 5):
        montando_cadastro = 10
        
    if (montando_cadastro == 10):
        if ((parentesco == 'wife of') or (parentesco == 'brother of')):
            cadastro_anterior = arquivo_do_documento[len(arquivo_do_documento) - 1]
            parente = cadastro_anterior[0]
        #print ("Cadastro montado:")
        #print (pessoa,parentesco,parente,profissao,num_doc,face_id,line_id)
        auxiliar = "".join(commodity_do_doc)
        arquivo_do_documento.append([pessoa,parentesco,parente,profissao,papel_atual,num_doc,face_comeco_cadastro, linha_comeco_cadastro, auxiliar])
        if (papel_atual == 'L'):
            papel_L_gravado = 1
        montando_cadastro = 0
        pessoa = ''
        parentesco = ''
        parente = '' 
        profissao = ''       
    
    if (montando_nome == 1):
        return
    
    if (montando_nome == 2 and pessoa == "" and montando_cadastro ==0):
        pessoa = limpa(nome)
        face_comeco_cadastro = face_id
        linha_comeco_cadastro = line_id
        montando_cadastro = 2
        return    
    
    if (montando_nome == 2 and pessoa != '' and parentesco != ''):
        parente = limpa(nome)
        montando_cadastro = 10
        return
    
    if(montando_cadastro != 0):    
        if (token_limpo_local in lista_de_profissoes):
            profissao = dicio[token_limpo_local]
            montando_cadastro = 5
            return
    
        if (token_limpo_local in lista_de_parentescos):
            parentesco = dicio[token_limpo_local]
            montando_cadastro = 3
            return 
   
    if (estado_atual == montando_cadastro and estado_atual != 0):
        montando_cadastro = 10
        
    return

# Machine 5: manages the role of the person whose name is being read, Lender, Borrower or Witness
def papel_pessoa(token_local,token_limpo_local):
    global papel_atual, papel_proximo
# se o token for ki, mudar estado: papel_atual = 'L'
# se papel_L_gravado != 0 (quer dizer que já gravou um nome de testemunha - para docs depois de 121 melhorar) 
#                         e papel_atual = 'L', mudar estado: papel_atual = 'B'
# se o token for igi ou i3-la2-e ou i3-ag2-e, mudar estado: papel_atual = 'W'


    if(papel_proximo == 'L' or papel_proximo == 'W'):
        papel_atual = papel_proximo
        papel_proximo = ''
        return
    
    if (token_limpo_local == 'ki'):
        papel_proximo = 'L'
    if (token_limpo_local == 'igi' or ("i3-la" in token_limpo_local) or ("i3-ag" in token_limpo_local)):
        papel_proximo = 'W'
    
    if(papel_L_gravado != 0 and papel_atual != 'W'):
        papel_atual = 'B'
    
    
    
    return

# Machine 6 : determina commodidity
# Adiciona um novo campo a cada cadastro, indicando qual é a commodity ou as commodities daquele documento
# O campo vem depois das linhas e é composto por uma ou mais das letras S, B e E, para silver, barley e emmer.
# A operação é feita pela identificação das palavras ku3-babbar, sze e ziz2
# Entretanto, sze é uma sílaba muito comum; o critério para esse caso deve ser ocorrência na primeira linha ou
# ocorrência de sze-am em alguma linha
def qual_commodity(token_local,token_limpo_local):
    global commodity_do_doc
    if(token_limpo_local == "ku3-babbar"):
        commodity_do_doc = commodity_do_doc | {"S"}
    if(token_limpo_local in {"sze", "sze-am"}): 
        commodity_do_doc = commodity_do_doc | {"B"}
#    if(token_limpo_local == "sze-am"):
#        commodity_do_doc = commodity_do_doc | {"B"}
    if(token_limpo_local == "ziz2"):
        commodity_do_doc = commodity_do_doc | {"E"}
    if(token_limpo_local == "gu2-gal"):
        commodity_do_doc = commodity_do_doc | {"C"}
    return

#Machine 7 : tracks amounts
#
#  Um amount pode começar quando:
#  - um amount não está na metade
#  - a último token não foi um número
#  - a último token não foi masz2
#  Isso é controlado na varíavel de estado:  esperando_amount = 1 se estiver esperando ou = 0 se estiver no meio de um amount
#  estados_amount = {'montando_juro','montando_amount','juro_montado','amount_montado','esperando_amount'}


def rastreia_amount(token_local, token_limpo_local):
    global estado_amount, amount_do_doc, juro_do_doc, valores_do_doc

#    print("Processando o token ", token_limpo_local)
    
    
    if(estado_amount == 'amount_montado'):
        #print("Document ", num_doc,". Amount =", amount_do_doc)
        if ("1(asz) gur-um 1(barig) 4(ban2)" not in amount_do_doc and 
           "1(asz) gur 1(barig) 4(ban2)" not in amount_do_doc and
           "1(asz) 1(barig) 4(ban2)" not in amount_do_doc):
            convertido = converte_amount(amount_do_doc)
#            #print(num_doc+"|"+amount_do_doc)
            convertido_quebrado = convertido.split(" ")
            #print("Convertido quebrado:", convertido_quebrado)
            
            if (convertido_quebrado[0] == "barley"):
                valores_do_doc[0] = valores_do_doc[0] + float(convertido_quebrado[1])
            if (convertido_quebrado[0] == "silver"):
                valores_do_doc[1] = valores_do_doc[1] + float(convertido_quebrado[1])
            if (convertido_quebrado[0] == "emmer"):
                valores_do_doc[2] = valores_do_doc[2] + float(convertido_quebrado[1])
            if (convertido_quebrado[0] == "chickpea"):
                valores_do_doc[3] = valores_do_doc[3] + float(convertido_quebrado[1])
            prata = valores_do_doc[1]*(0.0462963)
            amount_to_print = str(num_doc) + "|" + str(valores_do_doc[0]) + "|" + str(prata)+"|" + str(valores_do_doc[2]) + "|" + str(valores_do_doc[3])
            #print (amount_to_print)
            k.write(amount_to_print + "\n")
        commodity_aux = "unknown" 
        if ("ku3-babbar" in amount_do_doc):
            commodity_aux = "silver"
        if ("sze" in amount_do_doc):
            commodity_aux = "barley"
        if ("ziz2" in amount_do_doc):
            commodity_aux = "emmer"
        if ("gu2-gal" in amount_do_doc):
            commodity_aux = "chickpea"
        j.write(num_doc + "|" + "A" + "|"+ amount_do_doc + "|" + commodity_aux + "\n")
        amount_do_doc = ''
        commodity_aux = ''
    if(estado_amount == 'montando_amount'):
        amount_do_doc = amount_do_doc + " " + token_limpo_local
    if(estado_amount == 'juro_montado'):
        #print("Document ", num_doc,". Interest =", juro_do_doc)
        j.write(num_doc + "|" + "I" + "|"+ juro_do_doc + "\n")
        juro_do_doc = ''
    if(estado_amount == 'montando_juro'):
        juro_do_doc = juro_do_doc + " " + token_limpo_local
    
    if (estado_amount in ['esperando_amount','amount_montado','juro_montado']):
        if (token_limpo_local == 'masz2'):
            estado_amount = 'montando_juro'
        elif (re.match(r"[0-9]*\([a-z]*\)", token_limpo_local) or token_limpo_local == 'n'):
            estado_amount = 'montando_amount'
            amount_do_doc = token_limpo_local
        else:
            estado_amount = 'esperando_amount'

 #       print(estado_amount)
        return
# Há vários eventos que dizem que um amount está montado:
# a ocorrência do nome de uma comodite
    if (token_limpo_local in ['ziz2','ku3-babbar','sze','u3','gu2-gal']):
        if (estado_amount == 'montando_amount'):
            estado_amount = 'amount_montado'
        if (estado_amount == 'montando_juro'):
            estado_amount = 'juro_montado'
#        print(estado_amount)
        return
    
    
    if(estado_amount == 'montando_juro' and token_limpo_local in ['u2-s,a-ab']):
        estado_amount = 'juro_montado'
 #       print(estado_amount)
        return
    return
    



# Secondary iteration, the parsing
def parsing_iteration():
    global arquivo_do_documento
    if (int(num_doc) not in documentos_a_ler):
        return
    #print(num_doc)
    
    
    for token in list_of_tokens:
        token_limpo = limpa(token)
        # só pode distribuir os tokens quando eles forem do texto e não marcadores 
        # da posição
        if(updates_position(token)):
            qual_commodity(token, token_limpo)
            vai_montar_nome(token, token_limpo)
            vai_montar_cadastro(token,token_limpo)
            papel_pessoa(token, token_limpo)
            rastreia_amount(token, token_limpo)
            #print("Token distribuído: ",token, ". Montando_nome: ", montando_nome, ". Montando_cadastro", montando_cadastro)
    for cadastro in arquivo_do_documento:
        cadastro[8] = commodity_do_doc
        #f.write(pessoa + "|&" + parentesco + "|&" + parente + "|&" + profissao + "|&" + num_doc + "|&" + face_id + "|&" + line_id + "|&" + '\n')
        f.write(str(cadastro[0]) + "|&" + str(cadastro[1]) + "|&" + str(cadastro[2]) + "|&" + str(cadastro[3]) + "|&" + str(cadastro[4]) + "|&" + str(cadastro[5]) + "|&" + str(cadastro[6]) +
                "|&" + str(cadastro[7]) + "|&" + str(cadastro[8]) +
                "|&" + str(valores_do_doc[0]) + "|&" + str(valores_do_doc[1]) +
                "|&" + str(valores_do_doc[2]) + "|&" + str(valores_do_doc[3]) + '\n')
    #print(arquivo_do_documento)
    arquivo_do_documento = []
        
# Main iteration: to transform each document in a sequence of tokens; 
# tokens cannot be empty; cannot be line feeds either
# inside it we will call the secondary main iteration (the parsing itself)
e = io.open(base_folder+"/Processing_Input/00 cdli_atf_20170317.txt","r", encoding = "utf-8")
f = io.open(base_folder+"/Processing_Output/parsing"+run_date_out+".txt","w", encoding = "utf-8")
j = io.open(base_folder+"/Processing_Output/interests"+run_date_out+".txt","w", encoding = "utf-8")
k = io.open(base_folder+"/Processing_Output/amounts"+run_date_out+".txt","w", encoding = "utf-8")
list_of_tokens = []
for line in e:
    if (line == ''):
        continue
    if(line.startswith('#')):
        continue
    if(line.startswith('&')):
        if(already_have_doc == 1):
# tenho de adicionar um token para marcar o fim da lista. Em textos que terminam com um nome próprio, 
# a montagem do cadastro fica esperando um token que não tem nada a ver com nome para concluir o cadastro.
# Na ausência desse token, o cadastro acabaria figurando no próximo documento
            list_of_tokens.append('list')
            list_of_tokens.append('end')
    
            le_num_doc()
            parsing_iteration()
            list_of_tokens = []
            line_id = ''
            face_id = ''
            papel_atual = 'B'
            papel_L_gravado = 0
            commodity_do_doc = set()
            estado_amount = 'esperando_amount'
            amount_do_doc = ''
            commodity_aux = "-" 
            juro_do_doc = ''
            valores_do_doc = [0,0,0,0]
        already_have_doc = 1
    linha_quebrada = line.split(' ')
    for token in linha_quebrada:
        if (token != '' and token != '\n'):
            token = token.replace('\n','')
            list_of_tokens.append(token)
list_of_tokens.append('list')
list_of_tokens.append('end')
le_num_doc()
parsing_iteration() # this is for the last document loaded into memory
e.close()
f.close()
j.close()
k.close()


# In[ ]:





# In[ ]:




