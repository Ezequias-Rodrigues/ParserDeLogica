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
def extract_op(text, op):
    #Sei que é má prática MAAAAAAAAAAS acredito que dê para resolver isso usando splits ao invés de regex
    #   Desde já, peço seu perdão

    result = [text]
    matches = text.split(op,1)
    if(len(matches) > 1):
        result.extend(extract_op(matches[1], op))
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
        token_value = hex(token_count)  
        tokens[token_value] = [match, False]  
        var_to_tokens[match] = token_value  #
        token_count += 1
        text = text.replace(match, token_value)
        variable_lists.append(match)
    return text
def tokenize_exp(matches):
    global token_count
    last_var = None #Creio eu que o valor do token mais recente seja o mais aninhado, então ele deve ser o primeiro a ser substituído
    last_var_literal = "BCC"
    for match in matches:
        token_value = hex(token_count)  
        if(last_var and match.find(last_var_literal) != -1):
            aux = last_var_literal
            last_var_literal = match
            match = match.replace(aux, var_to_tokens[last_var])
        tokens[token_value] = [match, False]  # Armazenar o valor original e o valor booleano (inicialmente False, mas não faz diferença nesse momento)
        var_to_tokens[match] = token_value  
        last_var = match
        if(last_var_literal == "BCC"):
            last_var_literal = match
        token_count += 1  

text = " ((a.b)+c).(a.~(b>c)+d)>((~a+(b.(c+d))>e)>f)+x.y>z+i>j>k"
text_implication = "i>c+j>a.c.k>l"
all_matches = extract_op(text_implication, ">") 
 #nests_token[match.count("(")] = match #No caso de expressões com parenteses, determinar o nível de nesting é simples, basta contar o número de parênteses de abertura.

exp = extract_op(tokenize_var(text_implication), ">")
tokenize_exp(exp)
print(tokens)

#for match in all_matches:
   

   # print(implication_token)
   #print( nests_token)
    #print(f"Match: {match}")