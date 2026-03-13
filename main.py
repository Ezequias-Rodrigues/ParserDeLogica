import regex
token_count = 0
tokens = {} 
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

text = " ((a.b)+c) (a.(b>c)+d) ((a+(b.(c+d))>e)>f)"
all_matches = extract_all_parentheses(text)
for match in all_matches:
    print(f"Match: {match}")