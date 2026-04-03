import regex
class Parser:
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
    def __init__(self):
        self.token_count = 0
        self.tokens = {}  #tokens[VALOR HEX do token_count] = [VALOR ORIGINAL, Valor boolean no momento]
        self.var_to_tokens =  {} #Dicionario para mapear variáveis para seus tokens correspondentes, var_to_tokens[variável] = token
        self.variable_lists = []
        self.variable_amount = 0
        self.table_rows = 0
        self.op_pattern = r'([+\.=>#])' #Operadores disponiveis
        self.linear_parenthesis_pattern = r'([^()]*)'

    def extract_all_parentheses(self, text):
        
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
            inner = self.extract_all_parentheses(match[1:-1]) # Remove os parênteses externos antes de chamar recursivamente
            result.extend(inner)
        result.sort(key = lambda x: len(x)) #Mais complexas devem ficar por ultimo
        return result

    #Fora os parenteses, vou implementar a tokenização das expressões da de menor precedencia para a de maior, pq no caso dos parenteses, isso já é implicitamente resolvido
    def extract_op(self, text, op, r2l = True , result = None): #r2l = right to left, ou seja, se for True, a função vai extrair da direita para a esquerda, se não, da esquerda para a direita. Isso é necessário porque a maioria dos operadores lógicos tem associatividade à direita, ou seja, eles agrupam da direita para a esquerda.
        #Sei que é má prática MAAAAAAAAAAS acredito que dê para resolver isso usando splits ao invés de regex
        #Desde já, peço seu perdão
        exclude_keys = list(self.tokens.keys())
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
            
            if( not self.is_expr_low_complexity(matches[1])):    
                result = self.extract_op(matches[1], op, r2l, result)[::-1] #Desinverte pra inverter de novo na ultima iteração (papo de maluco, eu tlg)
            elif matches[1] != '' and not unbalancedMatch:
                result.append(matches[1])
        return result[::-1]#Invertendo a lista para poder tokenizar do menor para o maior 

    def solve_exp(self, expr): #Eu acredito que qualquer expressão lógica pode ser resumida em uma expressão de duas variaveis e um operador, por que no final ela sempre é ou True ou False
        if(type(expr) is bool): return expr


        exp_negated = expr.find("~(") != -1 #Aqui vai chegar sempre expressão simples, se tiver um ~( SEMPRE vai significar que ela é o inverso
        expr = expr.replace("~(", "").replace("(", "").replace(")","") #Se chegou até aqui, é pq n precisa de parenteses
        op = self.get_op(expr)
        

        if(op == None): #Sem operador = resolvido
            if(expr.find("~") != 1): #Tokens sem operadores também podem ser negados, ex: (~a)
                expr = expr.replace("~", "")
                return (not self.solve_exp(self.tokens[expr][0]) if expr in self.tokens.keys()
                         else not self.tokens[self.var_to_tokens[expr]] if expr in self.var_to_tokens.keys()
                           else None) if not expr in self.variable_lists else not self.tokens[self.var_to_tokens[expr]][1] #Digno de postar no r/programminghorror
            return (self.solve_exp(self.tokens[expr][0]) if expr in self.tokens.keys()
                     else self.tokens[self.var_to_tokens[expr]] if expr in self.var_to_tokens.keys()
                       else None) if not expr in self.variable_lists else self.tokens[self.var_to_tokens[expr]][1] #Sono faz a gente fazer coisas incriveis...

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
        
        A = self.tokens[matches[0]][0]
        B = self.tokens[matches[1]][0]
    
        if(A in self.variable_lists):
            A = self.tokens[self.var_to_tokens[A]][1]
        else:
            A = self.solve_exp(A)
        if(B in self.variable_lists):
            B = self.tokens[self.var_to_tokens[B]][1]
        else:
            B = self.solve_exp(B)

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
        if(exp_negated): result = not result
        return result
    
    def add_token(self, match):
        if(match in self.var_to_tokens): return self.var_to_tokens[match]

        if(self.count_op(match) == 0):
            match = match.replace("(", "").replace(")","") #Só para garantir que nenhum parenteses vai passar daqui aleatoriamente
        token_value = hex(self.token_count)  
        self.tokens[token_value] = [match, False]  
        self.var_to_tokens[match] = token_value  
        self.token_count += 1
        return token_value
    
    def tokenize_var(self, text): #Tokeniza as variaveis e substitui elas na expressão original para ser tokenizada novamente no futuro mas como expressões
        pattern = r'[aA-zZ]+' #Literalmente(trocadilho proposital) de a a Z, uma ou mais vezes
        matches = regex.findall(pattern, text, regex.VERSION1)

        for match in matches:
            if not match in self.variable_lists: #Evitar de tokenizar a mesma variável mais de uma vez
                
                text = text.replace(match, self.add_token(match))
                self.variable_lists.append(match)
        self.variable_amount = len(self.variable_lists)
        self.table_rows = 2 ** self.variable_amount
        return text

    def tokenize_exp(self, matches):
        last_var = [] 
        for match in matches:
            self.add_token(match)
            if(not match in last_var): last_var.append(match)
            self.token_count += 1  
        low_complexity = False
        while (not low_complexity):
            low_complexity = True
            for ltoken in self.tokens:
                token = self.tokens[ltoken][0]
                if not token in self.variable_lists:

                    pattern = r'[~]{0,1}^[^+\.=>#]*[+\.=>#][^+\.=>#]*$' #Checa se a expressão é de baixa complexidade, ou seja, se ela tem apenas um operador lógico
                    #Não usei a função pq eu havia esquecido dela KKKKKKK, se eu lembrar depois eu mudo #FIXME
                    
                    if(regex.match(pattern, token, regex.VERSION1) == None):
                        
                        for var in last_var:
                            if(var != token and token.find(var) != -1):
                                low_complexity = False
                                self.tokens[ltoken][0] = token.replace(var, self.var_to_tokens[var])
                            

    def get_op(self, exp):
        op = regex.search(self.op_pattern, exp, regex.VERSION1) #Pega o operador lógico da expressão, assumindo que só tem um operador lógico na expressão
        if(op == None): return None #Sem operadores
        else: op = op.group(0)
        return op

    def is_expr_low_complexity(self, expr):
        op = self.get_op(expr)
        if(op == None): return False
        pattern = rf'([^{op}]+)\{op}([^{op}]+)' #Formata o padrão da regex pra usar o operador op, não botei fé quando isso funcionou
        if(regex.match(pattern, expr, regex.VERSION1) == None): return False    
        matches = regex.findall(pattern, expr, regex.VERSION1)[0]
        for i in matches:
            if(not self.is_expr_low_complexity(i)):
                return False
        return matches

    def create_truth_table(self):
        table = None
        for i in range(self.table_rows):
            if(table == None):
                table = [[False] * self.variable_amount]
            else:
                table.append([False] * self.variable_amount)
            rowBinValue = bin(i)[2:].zfill(self.variable_amount) #Gera o valor binário da linha atual, preenchendo com zeros à esquerda para garantir que tenha o mesmo número de dígitos que o número de variáveis
            for j in range(self.variable_amount):
                table[i][j] = rowBinValue[j] == '1'
        return table[::-1] #Invertendo a orientação da tabela para seguir oq a gente viu em aula, apesar de não fazer diferença

    def parse_truth_table(self, table):
        self.variable_lists.sort() #Não faria diferença aqui, PORÉM, é mais dificil de ler a tabela assim, e eu perdi uma quantidade de tempo que não me orgulho tentando arrumar um erro que não existia por causa dessa diferença
        trues = 0
        print("X - -  " ,self.variable_lists)
        for i in range(self.table_rows):
            for j in range(self.variable_amount):
                self.tokens[self.var_to_tokens[self.variable_lists[j]]][1] = table[i][j]   
            rexp = self.solve_exp(self.tokens[list(self.tokens.keys())[-1]][0])
            trues = trues + 1 if rexp else trues 
            #print(tokens)
            print(f"Linha {i+1}: {table[i]} = Resultado: {rexp}")
        
        print(f"\nEssa tabela apresenta uma: {"Tauntologia" if trues == self.table_rows else "Contingência" if trues != 0 else "Contradição"}")

    def tokenize_linear_exp(self, exp):
        for op in ['.', '#', '+', '>', '=']:
            while(op in exp and self.count_op(exp) > 1): #Itera o processo abaixo na exp até que só sobre um unico operador, oq indica que ela ta na forma final
                matches = self.find_low_complexity_exp(exp, op) #Tenta achar o token op na exp
                if(matches == []): break
                exp = self.replace_in_exp(exp, matches)#Simplifica a exp, e adiciona tokens para poder ser "desimplificada" posteriormente
        self.add_token(exp)
        return exp

    def linearize_parenthesis(self, extracted, matches):
        extracted.sort(key = lambda x: len(x))
        if(extracted == []): return matches #O que não tem remédio, remediado está
        outer = extracted[-1] #Guarda o valor do ultimo index, que deve ser o mais complexo depois do sort
        final_exp = "" #Essa vai ser a expressão final depois de convertida
        
        while(len(extracted) > 0):
            exp = extracted[0][1:-1] #Remove os parenteses iniciais para começar
            del extracted[0] #Tira da list para simplificar o loop
            exp = self.tokenize_linear_exp(exp)
            self.add_token(exp)
            final_exp = exp
            for i in range(len(extracted)):
                extracted[i] =  extracted[i].replace("("+exp+")", self.var_to_tokens[exp])   
        matches = matches.replace(outer, self.var_to_tokens[final_exp])

        return matches

    def is_linear(self, exp):
        return exp.count("(") == 0

    def replace_in_exp(self, exp, matches):
        for match in matches:
            token_value = 0x0
            if(not match in self.var_to_tokens):
                token_value = hex(self.token_count)
                self.tokens[token_value] = [match, None]  # Armazenar o valor original e o valor booleano 
                self.var_to_tokens[match] = token_value  
            else:
                token_value = self.var_to_tokens[match]
            exp = exp.replace(match, token_value )
            self.token_count += 1  
        return exp

    def count_op(self, exp):
        pattern = r'[+>\.=#]'
        return len(regex.findall(pattern, exp, regex.VERSION1))

    def find_low_complexity_exp(self, exp, op):
        pattern = rf'[(~a-zA-Z0-9_]+[{op}][~a-zA-Z0-9_)]+'
        matches = regex.findall(pattern, exp, regex.VERSION1)
        if(matches == None): print("Expressão Invalida ", exp, "com operador", op)
        return matches

    def solve(self, text):
        tokenized = self.tokenize_var(text)
        parenthesis_step = self.extract_all_parentheses(tokenized) if tokenized.count("(") > 0 else []
        
        while(not self.is_linear(tokenized)):
        
            tokenized = self.linearize_parenthesis(parenthesis_step, tokenized)
            self.tokenize_linear_exp(tokenized)
            parenthesis_step = (self.extract_all_parentheses(tokenized))
            if(not self.is_linear(tokenized)):
                tokenized = self.linearize_parenthesis(parenthesis_step, tokenized)
            self.tokens.popitem()
    
        self.tokenize_linear_exp(tokenized)
        self.parse_truth_table(self.create_truth_table())

    
def main():
    '''
     
    '''
    inp = ""
    while(1):
     

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
            v = Parser()
            if(inp == "exit" or inp == ""):
                return
            v.solve(inp)
            input("Pressione [Enter] para continuar")

if __name__ == "__main__":
    main()