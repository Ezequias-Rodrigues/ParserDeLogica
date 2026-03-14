from ast import expr

import regex
'''
Simbolos que pretendo usar:
- `.` para AND
- `+` para OR
- `>` para IMPLICAÇÃO
- `=` para BICONDICIONAL
- `~` para NEGACÃO
- `(` e `)` para delimitar expressões, não são obrigatórios, mas ajudam a definir a precedência das operações.
'''

token_count = 0

tokens = {}  #tokens[VALOR HEX do token_count] = [VALOR ORIGINAL, Valor boolean no momento]
var_to_tokens =  {} #Dicionario para mapear variáveis para seus tokens correspondentes, var_to_tokens[variável] = token
variable_lists = []
variable_amount = 0
table_rows = 0
op_pattern = r'([+\.=>])' #Operadores disponiveis
def extract_all_parentheses(text):
    
    #Não pretendo limitar a profundidade do nesting,
    #fui atrás de uma biblioteca que suporta recursão em regex, e encontrei a 'regex' que é uma extensão da biblioteca 're' do Python.
    #Ela permite usar a sintaxe (?R) para referenciar a expressão regular atual, o que é útil para lidar com estruturas nested como parênteses.
    
    result = []
    pattern = r'\((?:[^()]|(?R))*\)'
    
    #Esse padrão vai ser para criar "tokens" de expressões lógicas que estejam delimitada por parênteses, mais a frente será criado uma maneira de lidar com as outras expressões
    #seguindo o a regra de precedência.
    #Explicação do padrão:
    #- `\\(` : corresponde a um parêntese de abertura literal.
    #- `(` ... `)` : define um grupo de captura para o conteúdo dentro dos parênteses. Até o regex tem que ser nested...
    #- `(?: ... )` : define um grupo de não captura para o conteúdo dentro dos parênteses. Isso é necessário para evitar que o regex capture cada nível de parênteses como um grupo separado.
    #- `[^()]` : corresponde a qualquer caractere que não seja um parêntese. Isso garante que o regex possa lidar com texto dentro dos parênteses sem se confundir com os parênteses de abertura e fechamento.
    #- `|` : operador "or" para alternar entre os caracteres que não são parênteses e a recursão.
    #- `(?R)` : refere-se à expressão regular atual, permitindo recursão para lidar com parênteses nested.
     
    matches = regex.findall(pattern, text, regex.VERSION1)
    for match in matches:
        result.append(match)
        inner = extract_all_parentheses(match[1:-1]) # Remove os parênteses externos antes de chamar recursivamente
        result.extend(inner)
    result.sort(key = lambda x: len(x)) #Mais complexas devem ficar por ultimo
    return result

#Fora os parenteses, vou implementar a tokenização das expressões da de menor precedencia para a de maior, pq no caso dos parenteses, isso já é implicitamente resolvido
def extract_op(text, op, r2l = True , result = None): #r2l = right to left, ou seja, se for True, a função vai extrair da direita para a esquerda, se não, da esquerda para a direita. Isso é necessário porque a maioria dos operadores lógicos tem associatividade à direita, ou seja, eles agrupam da direita para a esquerda.
    #Sei que é má prática MAAAAAAAAAAS acredito que dê para resolver isso usando splits ao invés de regex
    #Desde já, peço seu perdão
    exclude_keys = list(tokens.keys())
    exclude_keys.append('') #Alguns splits podem ocasionar uma match vazia, oq é problematico pro tokenizador
    exclude_keys.append('(')
    exclude_keys.append(')')#As vezes um parenteses sozinho passa, idealmente eu deveria ir atrás do por quê, porém resolver aqui não afeta a funcionalidade do código
    
    if result == None:
        result = []
    if(r2l): matches = text.split(op,1)
    else: matches = text.rsplit(op,1)
    #print("OP", op , "Matches",matches,"Result", result,"Exclude", exclude_keys)
    isAlreadyStored = matches[0] in result #Evita duplicadas
    isExcluded =  matches[0] in exclude_keys  #Evita caracteres nulos e outros "artefatos" no código
    unbalancedMatch = matches[0].count("(") != matches[0].count(")") #Olha, não era pra chegar parenteses aberto aqui, PORÉM...
    if(text != matches[0]  and  not isExcluded and not isAlreadyStored and not unbalancedMatch): result.append(matches[0])
   # print("Match", matches[0], "Sole" ,isSoleVariable, "Excluded", isExcluded, "Stored", isAlreadyStored, "Result", result)
    if(len(matches) > 1 ):
        unbalancedMatch = matches[1].count("(") != matches[1].count(")")
        if( not is_expr_low_complexity(matches[1])):    
            result = extract_op(matches[1], op, r2l, result)[::-1] #Desinverte pra inverter de novo na ultima iteração (papo de maluco, eu tlg)
        elif matches[1] != '' and not unbalancedMatch:
            result.append(matches[1])
    return result[::-1]#Invertendo a lista para poder tokenizar do menor para o maior 

def solve_exp(expr): #Eu acredito que qualquer expressão lógica pode ser resumida em uma expressão de duas variaveis e um operador, por que no final ela sempre é ou True ou False
    if(type(expr) is bool): return expr
    global op_pattern
    exp_negated = expr.find("~(") != -1 #Aqui vai chegar sempre expressão simples, se tiver um ~( SEMPRE vai significar que ela é o inverso
    expr = expr.replace("~(", "").replace("(", "").replace(")","") #Se chegou até aqui, é pq n precisa de parenteses
    op = get_op(expr)

    if(op == None): #Sem operador = resolvido
        if(expr.find("~") != 1): #Tokens sem operadores também podem ser negados, ex: (~a)
            return not tokens[expr.replace("~", "")][1]
        return tokens[expr][1]
    
    pattern = rf'([^{op}]+)\{op}([^{op}]+)' #Formata o padrão da regex pra usar o operador op, não botei fé quando isso funcionou
    matches = list(regex.findall(pattern, expr, regex.VERSION1)[0]) #Convertendo para lista pq é mais facil de trabalhar com elas doq com tuples
    #Aqui vou ter que criar um jeito para lidar com negações
    mult = [True, True]
    
    if('~' in matches[0]):
        matches[0] = matches[0].replace('~', '') #Aqui eu registro que foi negado o valor, mais tiro o operador de negação pra evitar a fadiga
        mult[0] = False
    if('~' in matches[1]):
        matches[1] = matches[1].replace('~', '')
        mult[1] = False
   
    A = tokens[matches[0]][0]
    B = tokens[matches[1]][0]
  
    if(A in variable_lists):
        A = tokens[var_to_tokens[A]][1]
    else:
        A = solve_exp(A)
    if(B in variable_lists):
        B = tokens[var_to_tokens[B]][1]
    else:
        B = solve_exp(B)

    if(not mult[0]):A = not A
    if(not mult[1]):B = not B

    result = None
    match op:
        case ".":
            result =  ((A) and (B))
        case "+":  
            result =  ((A) or (B))
        case ">":
            result = (not (A)) or (B)
        case "=":  
            result = (A == B)

   # print("Matches ", matches)
   # print(expr, " A:", A, mult[0], "B:", B, mult[1], " OP:", op, " R:", result, " N:", exp_negated)       
    
    if(exp_negated): result = not result
    return result

def tokenize_var(text): #Tokeniza as variaveis e substitui elas na expressão original para ser tokenizada novamente no futuro mas como expressões
    pattern = r'[aA-zZ]+' #Literalmente(trocadilho proposital) de a a Z, uma ou mais vezes
    matches = regex.findall(pattern, text, regex.VERSION1)

    global token_count
    global variable_amount
    global table_rows
    for match in matches:
        if not match in variable_lists: #Evitar de tokenizar a mesma variável mais de uma vez
            token_value = hex(token_count)  
            tokens[token_value] = [match, False]  
            var_to_tokens[match] = token_value  #
            token_count += 1
            text = text.replace(match, token_value)
            variable_lists.append(match)
    variable_amount = len(variable_lists)
    table_rows = 2 ** variable_amount
    return text

def tokenize_exp(matches):
    global token_count
    last_var = [] 
    for match in matches:
        token_value = hex(token_count)
        tokens[token_value] = [match, False]  # Armazenar o valor original e o valor booleano (inicialmente False, mas não faz diferença nesse momento)
        var_to_tokens[match] = token_value  
        if(not match in last_var): last_var.append(match)
        token_count += 1  
    low_complexity = False
    while (not low_complexity):
        low_complexity = True
        for ltoken in tokens:
            token = tokens[ltoken][0]
            if not token in variable_lists:
                patterns = r'[~]{0,1}^[^+\.=>]*[+\.=>][^+\.=>]*$' #Checa se a expressão é de baixa complexidade, ou seja, se ela tem apenas um operador lógico
                #Não usei a função pq eu havia esquecido dela KKKKKKK, se eu lembrar depois eu mudo #FIXME
                if(regex.match(patterns, token, regex.VERSION1) == None):
                    for var in last_var:
                        if(var != token and token.find(var) != -1):
                            low_complexity = False
                            tokens[ltoken][0] = token.replace(var, var_to_tokens[var])

def tokenize_parenthesis(matches, text):
    #Aqui vou ter que fazer diferente da função acima, lá eu usei o tokens direto, aqui eu vou ter que criar uma variavel auxiliar
    #reduzir a complexidade das expressões nele, e depois inserir ela na tokens
    token_aux = {}
    var_aux = {}
    global token_count
    global tokens
    global var_to_tokens
    last_var = [] 
 
    for match in matches:
        token_value = hex(token_count)
        token_aux[token_value] = [match, False]  
        var_aux[match] = token_value  
        token_count += 1 #Vou incrementar o token aqui mesmo para facilitar as coisas
        if(not match in last_var): last_var.append(match)
   
    low_complexity = False
    while (not low_complexity):
        low_complexity = True 
        for ltoken in token_aux: 
            token = token_aux[ltoken][0]
            comp = is_parenthesis_low_complexity(token)
            
            if(not comp or type(comp) == tuple):
                for var in last_var:
                    
                    if(var != token and token.find(var) != -1):
                        low_complexity = False
                        token_aux[ltoken][0] = token.replace(var, var_aux[var])
   
    tokens = tokens | token_aux #Eu tive que pesquisar pra achar essa função... esse operador usualmente é pra operação bitwise em outras linguagens (inclusive em GDScript, que é baseado em Python)
    
    var_to_tokens = var_to_tokens | var_aux
    for token in list(var_aux.keys())[::-1]: #inverte a var para os MAIS COMPLEXOS ficarem na frente dessa vez, isso é pq o texto vai ser substituido, e ao invés de comparar cada valor com cada outro,
        #eu só altero ele no texto original, e vou dando replace simplificando ela
        if(token in text):
            text  = text.replace(token, var_aux[token])
    return text

def solve_tokens(rtokens):
    for token in rtokens:
        if not rtokens[token][0] in variable_lists: #Se o token não for uma variável, ou seja, se for uma expressão, ele deve ser resolvido
            if(type(is_expr_low_complexity(rtokens[token][0])) == tuple):
               rtokens[token][1] =  solve_exp(rtokens[token][0])
    
def get_op(exp):
    global op_pattern
    op = regex.search(op_pattern, exp, regex.VERSION1) #Pega o operador lógico da expressão, assumindo que só tem um operador lógico na expressão
    if(op == None): return None #Sem operadores
    else: op = op.group(0)
    return op

def is_expr_low_complexity(expr):
    op = get_op(expr)
    if(op == None): return False
    pattern = rf'([^{op}]+)\{op}([^{op}]+)' #Formata o padrão da regex pra usar o operador op, não botei fé quando isso funcionou
    if(regex.match(pattern, expr, regex.VERSION1) == None): return False    
    matches = regex.findall(pattern, expr, regex.VERSION1)[0]
    return matches

def is_parenthesis_low_complexity(expr):
    pattern = r'^\(.*\)$' #Pega qualquer coisa dentro de parenteses
    if(expr.count("(") > 1): return False #Nested é complexo
    if(regex.match(pattern, expr, regex.VERSION1) == None): return False
    expr = expr.replace("(", "").replace(")", "")
    return is_expr_low_complexity(expr)

def create_truth_table():
    table = None
    for i in range(table_rows):
        if(table == None):
            table = [[False] * variable_amount]
        else:
            table.append([False] * variable_amount)
        rowBinValue = bin(i)[2:].zfill(variable_amount) #Gera o valor binário da linha atual, preenchendo com zeros à esquerda para garantir que tenha o mesmo número de dígitos que o número de variáveis
        for j in range(variable_amount):
            table[i][j] = rowBinValue[j] == '1'
    return table[::-1] #Invertendo a orientação da tabela para seguir oq a gente viu em aula, apesar de não fazer diferença

def parse_truth_table(table):
    variable_lists.sort() #Não faria diferença aqui, PORÉM, é mais dificil de ler a tabela assim, e eu perdi uma quantidade de tempo que não me orgulho tentando arrumar um erro que não existia por causa dessa diferença
    print("X - -  " ,variable_lists)
    for i in range(table_rows):
        for j in range(variable_amount):
            tokens[var_to_tokens[variable_lists[j]]][1] = table[i][j]   
        solve_tokens(tokens)
        #print("Tokens:" , tokens)
        print(f"Linha {i+1}: {table[i]} = Resultado: {tokens[list(tokens.keys())[-1]][1]}")

def extract_exp(text): #A ordem de extração aqui é invertida, primeiro tira a bicondicional, depois implicação etc, o motivo é pq temos que quebrar do mais complexo pro menos complexo
   
    exp = extract_op(text, "=")#A bi condicional é mais complexa, pois por ser a ultima, é a que pode ter mais expressões nested nela.
    aux = exp[:]#Sempre q vc ver essa linha, significa q uma copia dos valores de exp foi feita para aux, isso pq o tamanho de exp vai ser alterado conforme as expressões são extraidas
    #Não da pra fazer aux = exp pq dessa forma vc diz q aux é uma referencia de exp, e toda vez que você modificar um dos dois, vc modifica o outro. No caso desse código, isso causaria um loop infinito
    
    if(len(exp) > 0): #Caso tenha sido extraido expressões da bicondicional, da para usar as expressões nested nela para dar continuidade, e tentar extrair a implicação
        for e in exp:
            if(e.find("=") == -1):
                aux = extract_op(e, ">", True, exp)
            exp = aux[:]
    else: exp = extract_op(text, ">", True, exp) #Porem, toda via, entretanto, caso não haja uma bicondicional, tenta extrair as expressões nested na implicação apartir do texto inicial
    if(len(exp) > 0): #E assim vai
        for e in exp:
            if(e.find(">") == -1):
                aux = (extract_op(e, "+", False, exp))
            exp = aux[:]
    else: exp = extract_op(text, "+", False, exp)
    if(len(exp) > 0): 
        for e in exp:
            if(e.find("+") == -1):
                aux = (extract_op(e, ".", False, exp))
            exp = aux[:]
    else: exp = extract_op(text, ".", False, exp)
    
    exp.append(text)#Ao final de tudo, adiciona a expressão original(bem, quase original, ela já está tokenizada) na lista de expressões
    exp.sort(key = lambda x: len(x)) #Organiza a lista de expressões do menos complexos(no caso desse algoritmo em especifico, complexidade =  tamanho da string) para o mais complexo
    return exp

text = "abacate.banana+carambola>(~(abacate.carambola)+carambola)" #Variaveis infinitas, com infinitos caracteres (em teoria )

tokenized = tokenize_var(text)
parenthesis_step = extract_all_parentheses(tokenized) if tokenized.count("(") > 0 else []

if(parenthesis_step == []): #Sem parentheses na equação, então evita tentar tokenizar parenteses pra compensar pelas má otimizações que fiz KKKK
    exp_extracted = extract_exp(tokenized)
    tokenize_exp(exp_extracted) #Tokeniza linearmente
else:
    exp_extracted = []
    for exp in parenthesis_step: #Aqui a tokenização precisa se aprofundar, então tokeniza os parenteses mais internos primeiro, e depois os mais externos, a ordem deles ja foi definida em extract_all_parentheses
        if(is_parenthesis_low_complexity(exp) or not get_op(exp)):
            exp_extracted.append(exp)
        else:
            exp_extracted.extend(extract_exp(exp))
    tokenize_exp(extract_exp(tokenize_parenthesis(exp_extracted, tokenized)))
parse_truth_table(create_truth_table())

