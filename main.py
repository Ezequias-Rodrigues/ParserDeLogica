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
nests_token = {} #nests_token[X] = [token1, token2, ...] onde X é representa o nivel de nesting que a expressão possui, e token1, token2, ... são os tokens que estão naquele nível de nesting.
implication_token = {} #mesmo esquema mas com >
or_token = {} 
and_token = {} 

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
    return result
#Fora os parenteses, vou implementar a tokenização das expressões da de menor precedencia para a de maior, pq no caso dos parenteses, isso já é implicitamente resolvido
def extract_op(text, op, r2l = True , result = None): #r2l = right to left, ou seja, se for True, a função vai extrair da direita para a esquerda, se não, da esquerda para a direita. Isso é necessário porque a maioria dos operadores lógicos tem associatividade à direita, ou seja, eles agrupam da direita para a esquerda.
    #Sei que é má prática MAAAAAAAAAAS acredito que dê para resolver isso usando splits ao invés de regex
    #   Desde já, peço seu perdão
    exclude_keys = list(tokens.keys())
    if(not text in variable_lists and not text in exclude_keys and(result == None or not text in result)): #Essas checagens contra a variable_list é para evitar que uma proposição sem operador seja colocado nessa lista
        if(result == None):
            result = [text]
        else:
            result.append(text)
    else:
        result = []
    if(r2l): matches = text.split(op,1)
    else: matches = text.rsplit(op,1)
   
    if(text != matches[0] and not matches[0] in variable_lists and  not matches[0] in exclude_keys and not matches[0] in result ): result.append(matches[0])
    if(len(matches) > 1):
        result.extend(extract_op(matches[1], op)[::-1]) #Desinverte pra inverter de novo na ultima iteração
    return result[::-1]#Invertendo a lista para poder tokenizar do menor para o maior 
def solve_exp(expr, op): #Eu acredito que qualquer expressão lógica pode ser resumida em uma expressão de duas variaveis e um operador, por que no final ela sempre é ou True ou False
    pattern = rf'([^{op}]+)\{op}([^{op}]+)' #Formata o padrão da regex pra usar o operador op, não botei fé quando isso funcionou
    matches = regex.findall(pattern, expr, regex.VERSION1)[0]
    #mockando valores booleanos para testar a função, depois eu substituo pelos tokens
    mtokens = {matches[0]: False, matches[1]: False}

    match op:
        case ".":
            return mtokens[matches[0]] and mtokens[matches[1]]
        case "+":  
            return mtokens[matches[0]] or mtokens[matches[1]]
        case ">":
            return not mtokens[matches[0]] or mtokens[matches[1]]
        case "=":
            return mtokens[matches[0]] == mtokens[matches[1]]

    pass
def tokenize_var(text): #Tokeniza as variaveis e substitui elas na expressão original para ser tokenizada novamente no futuro mas como expressões
    pattern = r'[aA-zZ]+'
    matches = regex.findall(pattern, text, regex.VERSION1)
    global token_count
    for match in matches:
        if not match in variable_lists: #Evitar de tokenizar a mesma variável mais de uma vez
            token_value = hex(token_count)  
            tokens[token_value] = [match, False]  
            var_to_tokens[match] = token_value  #
            token_count += 1
            text = text.replace(match, token_value)
            variable_lists.append(match)
    return text
def tokenize_exp(matches):
    global token_count
    last_var = [] 
    last_var_literal = [] 
    for match in matches:
        token_value = hex(token_count)
        c = 0
        if(not match in last_var_literal): last_var_literal.append(match)
        for i in last_var:
          #  if(match != last_var_literal[c] and match.find(last_var_literal[c]) != -1):   
             #   match = match.replace(last_var_literal[c], var_to_tokens[i])
            c += 1

        tokens[token_value] = [match, False]  # Armazenar o valor original e o valor booleano (inicialmente False, mas não faz diferença nesse momento)
        var_to_tokens[match] = token_value  
        if(not match in last_var): last_var.append(match)
        token_count += 1  
    print(last_var)
    low_complexity = False
    while (not low_complexity):
        low_complexity = True
        for ltoken in tokens:
            token = tokens[ltoken][0]
            if not token in variable_lists:
                patterns = r'^[^+\.=>]*[+\.=>][^+\.=>]*$' #Checa se a expressão é de baixa complexidade, ou seja, se ela tem apenas um operador lógico
                if(regex.match(patterns, token, regex.VERSION1) == None):
                    low_complexity = False
                    for var in last_var:
                        if(var != token and token.find(var) != -1):
                            tokens[ltoken][0] = token.replace(var, var_to_tokens[var])
    print(tokens)
    #aux = last_var[:]
   # c = 0
   # new_exps = {}
  #  for i in aux:
      ##  for j in aux:
          #  if(i != j and j.find(i) != -1):
            #    if(not j in new_exps): new_exps[j] = [i]
              #  elif(len(var_to_tokens[i]) > len(new_exps[j])): new_exps[j].append(i)
               
                #last_var[c] = j.replace(i, var_to_tokens[i])
     #   c += 1
   # for i in new_exps:
  #     
      #  for j in new_exps[i]:
           # print(j, i, j in i  and j != i)
       # new_exps[i] =  i.replace(new_exps[i], var_to_tokens[new_exps[i]])
  #  last_var = list(new_exps.keys())
   # print("New exps: ", new_exps)

def solve_tokens(rtokens):
    for token in rtokens:
        if not rtokens[token][0] in variable_lists: #Se o token não for uma variável, ou seja, se for uma expressão, ele deve ser resolvido
           print(token, rtokens[token])
    print(var_to_tokens)

text = " ((a.b)+c).(a.~(b>c)+d)>((~a+(b.(c+d))>e)>f)+x.y>z+i>j>k"
#text_implication = "i>c+j>a.c.k>l"
text_implication = "t.p+q>b>r.s+t>i"

 #nests_token[match.count("(")] = match #No caso de expressões com parenteses, determinar o nível de nesting é simples, basta contar o número de parênteses de abertura.
tokenize_var(text_implication)

#exp = extract_op(tokenize_var(text_implication), ">") Por enquanto vou trocar essa pela expressão real por questões de legibilidade
exp = extract_op(text_implication, "=") 
aux = exp[:]

for e in exp:
    if(e.find("=") == -1):
        aux.extend(extract_op(e, ">", True, exp))
exp = aux[:]
for e in exp:
    if(e.find(">") == -1):
        aux.extend(extract_op(e, "+", False, exp))
exp = aux[:]
for e in exp:
    if(e.find("+") == -1):
        aux.extend(extract_op(e, ".", False, exp))

#exp1 = exp[:] #Copia de valores para não entrar num loop infinito
exp.sort(key = lambda x: len(x))
tokenize_exp(exp)

#solve_tokens(tokens)

#for match in all_matches:
   

   # print(implication_token)
   #print( nests_token)
    #print(f"Match: {match}")