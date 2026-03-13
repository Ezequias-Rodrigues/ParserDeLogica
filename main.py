import regex
'''
Simbolos que pretendo usar:
- `.` para AND
- `+` para OR
- `>` para IMPLICAÇÃO
- `~` para NEGACÃO
- `(` e `)` para delimitar expressões, não são obrigatórios, mas ajudam a definir a precedência das operações.
- TALVEZ, MUITO TALVEZ, eu implemente bicondicionais, mas vamos ver o quão difícil é lidar com as outras operações primeiro.
'''

token_count = 0

tokens = {}  #tokens[VALOR HEX TO token_count] = VALOR ORIGINAL
nests_token = {} #nests_token[X] = [token1, token2, ...] onde X é representa o nivel de nesting que a expressão possui, e token1, token2, ... são os tokens que estão naquele nível de nesting.
implication_token = {} #mesmo esquema mas com >
def extract_all_parentheses(text):
    '''
    Não pretendo limitar a profundidade do nesting,
    fui atrás de uma biblioteca que suporta recursão em regex, e encontrei a 'regex' que é uma extensão da biblioteca 're' do Python.
    Ela permite usar a sintaxe (?R) para referenciar a expressão regular atual, o que é útil para lidar com estruturas nested como parênteses.
    '''
    result = []
    pattern = r'\((?:[^()]|(?R))*\)'
    '''
    Esse padrão vai ser para criar "tokens" de expressões lógicas que estejam delimitada por parênteses, mais a frente será criado uma maneira de lidar com as outras expressões
    seguindo o a regra de precedência.
    Explicação do padrão:
    - `\\(` : corresponde a um parêntese de abertura literal.
    - `(` ... `)` : define um grupo de captura para o conteúdo dentro dos parênteses. Até o regex tem que ser nested...
    - `(?: ... )` : define um grupo de não captura para o conteúdo dentro dos parênteses. Isso é necessário para evitar que o regex capture cada nível de parênteses como um grupo separado.
    - `[^()]` : corresponde a qualquer caractere que não seja um parêntese. Isso garante que o regex possa lidar com texto dentro dos parênteses sem se confundir com os parênteses de abertura e fechamento.
    - `|` : operador "or" para alternar entre os caracteres que não são parênteses e a recursão.
    - `(?R)` : refere-se à expressão regular atual, permitindo recursão para lidar com parênteses nested.
     '''
    matches = regex.findall(pattern, text, regex.VERSION1)
    for match in matches:
        result.append(match)
        inner = extract_all_parentheses(match[1:-1]) # Remove os parênteses externos antes de chamar recursivamente
        result.extend(inner)
    return result
#Fora os parenteses, vou implementar a tokenização das expressões da de menor precedencia para a de maior, pq no caso dos parenteses, isso já é implicitamente resolvido
def extract_op(text, op):
    ''' Sei que é má prática MAAAAAAAAAAS acredito que dê para resolver isso usando splits ao invés de regex
        Desde já, peço seu perdão
    '''
    result = [text]
    matches = text.split(">",1)
    if(len(matches) > 1):
        result.extend(extract_op(matches[1], op))
       
    return result
text = " ((a.b)+c) (a.~(b>c)+d) ((~a+(b.(c+d))>e)>f) x.y>z i>j>k"
text_implication = "i>j>k>l"
all_matches = extract_op(text_implication, ">")
for match in all_matches:
    #nests_token[match.count("(")] = match #No caso de expressões com parenteses, determinar o nível de nesting é simples, basta contar o número de parênteses de abertura.
    implication_token[match.count(">")] = match 
    print(implication_token)
   #print( nests_token)
    print(f"Match: {match}")