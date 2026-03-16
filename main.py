from ast import expr

import regex
'''
Simbolos que pretendo usar:
- `.` para AND
- `#` para XOR (o ^ é usado pra regex, e como eu to implementando isso depois eu REALMENTE não quero mexer muito nas regex que já estão funcionando)
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
op_pattern = r'([+\.=>#])' #Operadores disponiveis

def clear():
    global token_count
    global tokens
    global var_to_tokens
    global variable_lists
    global variable_amount
    global table_rows
    token_count = 0
    tokens = {}  
    var_to_tokens =  {} 
    variable_lists = []
    variable_amount = 0
    table_rows = 0

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
        case "#":
            result = (A ^ B)

   # print("Matches ", matches)
    #print(expr, " A:", A, mult[0], "B:", B, mult[1], " OP:", op, " R:", result, " N:", exp_negated)       
    
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

                pattern = r'[~]{0,1}^[^+\.=>#]*[+\.=>#][^+\.=>#]*$' #Checa se a expressão é de baixa complexidade, ou seja, se ela tem apenas um operador lógico
                #Não usei a função pq eu havia esquecido dela KKKKKKK, se eu lembrar depois eu mudo #FIXME
                
                if(regex.match(pattern, token, regex.VERSION1) == None):
                    
                    for var in last_var:
                        if(var != token and token.find(var) != -1):
                            low_complexity = False
                            tokens[ltoken][0] = token.replace(var, var_to_tokens[var])
                        

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
    for i in matches:
        if(not is_expr_low_complexity(i)):
            return False
    return matches

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

        print(f"Linha {i+1}: {table[i]} = Resultado: {solve_exp(tokens[list(tokens.keys())[-1]][0])}")

def tokenize_linear_exp(exp):
    global token_count
    for op in ['.', '#', '+', '>', '=']: 
        while(op in exp and count_op(exp) > 1): #Itera o processo abaixo na exp até que só sobre um unico operador, oq indica que ela ta na forma final
            
            matches = find_low_complexity_exp(exp, op) #Tenta achar o token op na exp
            exp = replace_in_exp(exp, matches)#Simplifica a exp, e adiciona tokens para poder ser "desimplificada" posteriormente
    token_value = hex(token_count)
    tokens[token_value] = [exp, None]  #Finalmente, adicionamos a exp final pra lista de tokens
    var_to_tokens[exp] = token_value  
    token_count += 1  
    return exp

def linearize_parenthesis(extracted, matches):
    global token_count
    extracted.sort(key = lambda x: len(x))
    if(extracted == []): return matches #O que não tem remédio, remediado está
    outer = extracted[-1] #Guarda o valor do ultimo index, que deve ser o mais complexo depois do sort
    final_exp = "" #Essa vai ser a expressão final depois de convertida
    
    while(len(extracted) > 0):
        exp = extracted[0][1:-1] #Remove os parenteses iniciais para começar
        del extracted[0] #Tira da list para simplificar o loop
        token_value = hex(token_count)
        tokens[token_value] = [exp, None]  
        var_to_tokens[exp] = token_value  
        token_count += 1  
        final_exp = exp
        for i in range(len(extracted)):
           
            extracted[i] =  extracted[i].replace("("+exp+")", var_to_tokens[exp])   
    matches = matches.replace(outer, var_to_tokens[final_exp])
    return matches

def replace_in_exp(exp, matches):
    global token_count
    for match in matches:
        token_value = 0x0
        if(not match in var_to_tokens):
            token_value = hex(token_count)
            tokens[token_value] = [match, None]  # Armazenar o valor original e o valor booleano 
            var_to_tokens[match] = token_value  
        else:
            token_value = var_to_tokens[match]
        exp = exp.replace(match, token_value )
        token_count += 1  
    return exp

def count_op(exp):
    pattern = r'[+>.=#]'
    return len(regex.findall(pattern, exp, regex.VERSION1))

def find_low_complexity_exp(exp, op):
    pattern = rf'[a-zA-Z0-9_]+[{op}][a-zA-Z0-9_]+'
    matches = regex.findall(pattern, exp, regex.VERSION1)
    if(matches == None): print("Expressão Invalida ", exp, "com operador", op)
    return matches

def solve(text):
    tokenized = tokenize_var(text)
    parenthesis_step = extract_all_parentheses(tokenized) if tokenized.count("(") > 0 else []
    while(parenthesis_step != []):
        tokenized = linearize_parenthesis(parenthesis_step, tokenized)
        parenthesis_step = (extract_all_parentheses(tokenized))
        tokenized = linearize_parenthesis(parenthesis_step, tokenized)
    tokenize_linear_exp(tokenized)
    parse_truth_table(create_truth_table())
    input("\nPressione ENTER para continuar...\n")

def main():
    #text = "abacate.banana+carambola>(~(abacate.carambola)+carambola)" #Variaveis infinitas, com infinitos caracteres (em teoria )
    #text = "a.(b+c+(a.c+(a>b)))>c"
    #text = "a.b+c+a.c+a>b>c"
    #text = "a.b+c+a.c+a>b>c+a.b"
    #text = "(((a.b)>(c+a))=((b>c).(a+c)))+(a.(b>c))"
    inp = ""
    while(1):
            clear()
        #try:
            print(
                "\nSimbolos disponíveis:\n"\
                "- `.` para AND\n"\
                "- `+` para OR\n"\
                "- `>` para IMPLICAÇÃO\n"\
                "- `=` para BICONDICIONAL\n"\
                "- `~` para NEGACÃO\n"\
                "- `(` e `)` para delimitar expressões, não são obrigatórios, mas ajudam a definir a precedência das operações.\n" \
                "Nota: Evite utilizar nomes de váriaveis com sequências de caracteres repetidas, ex: AAAAA, BABABABA etc\n"\
                "Digite `exit` para sair\n"\
                "Favor reportar qualquer erro que encontrar.\n"
            )
            inp = input("Digite sua equação: ").replace(" ", "")
            if(inp == "exit" or inp == ""):
                return
            solve(inp)
        #except:
          #  print("Verifique sua equação, não foi possível interpretar ela (", inp, ")")
            #input("\nPressione ENTER para continuar...\n")

if __name__ == "__main__":
    main()