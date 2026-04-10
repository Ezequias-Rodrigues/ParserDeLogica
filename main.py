import regex
class patterns:
    PROPOSITIONS = r'[a-zA-Z0-9]+' #Literalmente(trocadilho proposital) de a a Z, uma ou mais vezes'[a-zA-Z0-9]+' #Literalmente(trocadilho proposital) de a a Z, uma ou mais vezes
    TOKENS =  r'(0x\d+)'
    NEGATED_TOKENS =  r'([~]{0,1}0x\d+)'
    OPERATOR = r'([+\.=>^])'
    PARENTHESIS = r'([^()]*)'
    RECURSIVE_PARENTHESIS = r'\((?:[^()]|(?R))*\)'
        #Esse padrão vai ser para criar "tokens" de expressões lógicas que estejam delimitada por parênteses, mais a frente será criado uma maneira de lidar com as outras expressões
        #seguindo o a regra de precedência.
        #Explicação do padrão:
        #- `\\(` : corresponde a um parêntese de abertura literal.
        #- `(` ... `)` : define um grupo de captura para o conteúdo dentro dos parênteses. Até o regex tem que ser nested...
        #- `(?: ... )` : define um grupo de não captura para o conteúdo dentro dos parênteses. Isso é necessário para evitar que o regex capture cada nível de parênteses como um grupo separado.
        #- `[^()]` : corresponde a qualquer caractere que não seja um parêntese. Isso garante que o regex possa lidar com texto dentro dos parênteses sem se confundir com os parênteses de abertura e fechamento.
        #- `|` : operador "or" para alternar entre os caracteres que não são parênteses e a recursão.
        #- `(?R)` : refere-se à expressão regular atual, permitindo recursão para lidar com parênteses nested.
    SIMPLE_EXPRESSION_WILDCARD = r'([^*]+)\*([^*]+)' #Derivado de rf'([^{op}]+)\{op}([^{op}]+)', aceita sentenças
    FINAL_EXPRESSION_WILDCARD = r'[(~a-zA-Z0-9_]+[\*][~a-zA-Z0-9_)]+' #Derivada de [(~a-zA-Z0-9_]+[\{op}][~a-zA-Z0-9_)]+, quase a mesma coisa da anterior mas só aceita proposições e não sentenças
    CONTRADICTION = r'(?:(0x[0-9a-f]+)\.~\1)|(?:~(0x[0-9a-f]+)\.\2)' #XORzinho de praxe
class Parser:
    def __init__(self):
        self.token_count = 0
        self.tokens = {}  #tokens[VALOR HEX do token_count] = [VALOR ORIGINAL, Valor boolean no momento]
        self.tokens_canon_and_equivalent = {}
        self.tokens_canon_or_equivalent = {}
        self.tokens_simplified = {}
        self.var_to_tokens =  {} #Dicionario para mapear variáveis para seus tokens correspondentes, var_to_tokens[variável] = token
        self.variable_lists = []
        self.variable_amount = 0
        self.table_rows = 0
        self.table = None
        self.table_len = 0


    def extract_all_parentheses(self, text):
        
        #Não pretendo limitar a profundidade do nesting,
        #fui atrás de uma biblioteca que suporta recursão em regex, e encontrei a 'regex' que é uma extensão da biblioteca 're' do Python.
        #Ela permite usar a sintaxe (?R) para referenciar a expressão regular atual, o que é útil para lidar com estruturas nested como parênteses.
        
        result = []
        matches = regex.findall(patterns.RECURSIVE_PARENTHESIS, text, regex.VERSION1)
        for match in matches:
            result.append(match)
            inner = self.extract_all_parentheses(match[1:-1]) # Remove os parênteses externos antes de chamar recursivamente
            result.extend(inner)
        result.sort(key = lambda x: len(x)) #Mais complexas devem ficar por ultimo
        return result

    #Fora os parenteses, vou implementar a tokenização das expressões da de menor precedencia para a de maior, pq no caso dos parenteses, isso já é implicitamente resolvido
    def extract_op(self, text, op, r2l = True , result = None): #r2l = right to left, ou seja, se for True, a função vai extrair da direita para a esquerda, se não, da esquerda para a direita. Isso é necessário porque a maioria dos operadores lógicos tem associatividade à direita, ou seja, eles agrupam da direita para a esquerda.
        exclude_keys = list(self.tokens.keys())
        #Alguns splits podem ocasionar uma match vazia, oq é problematico pro tokenizador
        exclude_keys = exclude_keys + ["", " ", "(", ")"]#As vezes um parenteses sozinho passa, idealmente eu deveria ir atrás do por quê, porém resolver aqui não afeta a funcionalidade do código
        if result == None:
            result = []
        if(r2l): matches = text.split(op,1)
        else: matches = text.rsplit(op,1)
        #print("OP", op , "Matches",matches,"Result", result,"Exclude", exclude_keys)
        isAlreadyStored = matches[0] in result #Evita duplicadas
        isExcluded =  matches[0] in exclude_keys  #Evita caracteres nulos e outros "artefatos" no código
        unbalancedMatch = matches[0].count("(") != matches[0].count(")")
        if(text != matches[0]  and  not isExcluded and not isAlreadyStored and not unbalancedMatch): result.append(matches[0])
        if(len(matches) > 1 ):
            unbalancedMatch = matches[1].count("(") != matches[1].count(")")
            
            if( not self.is_expr_low_complexity(matches[1])):    
                result = self.extract_op(matches[1], op, r2l, result)[::-1] #Desinverte pra inverter de novo na ultima iteração (papo de maluco, eu tlg)
            elif matches[1] != '' and not unbalancedMatch:
                result.append(matches[1])
        return result[::-1]#Invertendo a lista para poder tokenizar do menor para o maior 

    def solve_exp(self, expr): #Eu acredito que qualquer expressão lógica pode ser resumida em uma expressão de duas variaveis e um operador, por que no final ela sempre é ou True ou False
        if(type(expr) is bool): return expr
        while(expr.find("~~") != -1):
            expr = expr.replace("~~", "") #Isso aqui deve lidar com a dupla negação. Existem técnicas para distribuir a negação para as expressões, e as vezes, fazendo na mão, a dupla negação é util, mas nesse algoritmo isso não faz diferença
        exp_negated = expr.find("~(") != -1 #Aqui vai chegar sempre expressão simples, se tiver um ~( SEMPRE vai significar que ela é o inverso
        expr = expr.replace("~(", "").replace("(", "").replace(")","") #Se chegou até aqui, é pq n precisa de parenteses
        op = self.get_op(expr)

        if(op == None): #Sem operador = resolvido
            afirmative = (expr.find("~") == -1)
            if(not afirmative): expr = expr.replace("~", "")
            is_token = expr in self.tokens.keys()
            is_exp =   expr in self.var_to_tokens.keys()
            is_variable = expr in self.variable_lists
            ret = None
            if(is_token):
                ret = self.solve_exp(self.tokens[expr][0])
            elif(is_exp):
                ret = self.tokens[self.var_to_tokens[expr]][1]
            elif(is_variable):
                ret = self.tokens[self.var_to_tokens[expr]][1]
            if(not afirmative and ret != None): ret = not ret
            return ret
        
        matches = list(regex.findall(patterns.SIMPLE_EXPRESSION_WILDCARD.replace("*", op), expr, regex.VERSION1)[0]) #Convertendo para lista pq é mais facil de trabalhar com elas doq com tuples
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

        if(A.lower() == "false"):
            A = False
        elif (A.lower() == "true"): #Isso aqui é cursed d+
            A = True
        elif(A in self.variable_lists):
            A = self.tokens[self.var_to_tokens[A]][1]
        else:
            A = self.solve_exp(A)

        if(B.lower() == "false"):
            B = False
        elif (B.lower() == "true"): #Isso aqui é cursed d+
            B = True
        elif(B in self.variable_lists):
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
            case "^":
                result = (A ^ B)
        if(exp_negated): result = not result
        return result
    
    def add_token(self, match):

        if(match in self.var_to_tokens): return self.var_to_tokens[match]
        if(match in self.tokens): return match

        if(self.count_op(match) == 0):
            match = match.replace("(", "").replace(")","") #Só para garantir que nenhum parenteses vai passar daqui aleatoriamente
        while(match.find("~~") != -1):
            match = match.replace("~~", "") #Lidando com dupla negação aqui também, pois dupla negação com parenteses não é pega na proxima etapa
        if(match in self.var_to_tokens): return self.var_to_tokens[match]
     
        token_value = hex(self.token_count)  
        self.tokens[token_value] = [match, False]  
        self.var_to_tokens[match] = token_value  
        self.token_count += 1
        return token_value
    
    def tokenize_var(self, text): #Tokeniza as variaveis e substitui elas na expressão original para ser tokenizada novamente no futuro mas como expressões
        matches = regex.findall(patterns.PROPOSITIONS, text, regex.VERSION1)

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
                    if(self.is_expr_low_complexity(token)):
                        for var in last_var:
                            if(var != token and token.find(var) != -1):
                                low_complexity = False
                                self.tokens[ltoken][0] = token.replace(var, self.var_to_tokens[var])
                            

    def get_op(self, exp):
        op = regex.search(patterns.OPERATOR, exp, regex.VERSION1) #Pega o operador lógico da expressão, assumindo que só tem um operador lógico na expressão
        if(op == None): return None #Sem operadores
        else: op = op.group(0)
        return op

    def is_expr_low_complexity(self, expr):
        op = self.get_op(expr)
        if(op == None): return False
        if(regex.match(patterns.SIMPLE_EXPRESSION_WILDCARD.replace("*", op), expr, regex.VERSION1) == None): return False    
        matches = regex.findall(patterns.SIMPLE_EXPRESSION_WILDCARD.replace("*", op), expr, regex.VERSION1)[0]
        for i in matches:
            if(not self.is_expr_low_complexity(i)):
                return False
        return matches
        
    def create_canon_equivalence(self, tokens_list, operator):
        for token_id in self.tokens:
            token = self.tokens[token_id][0]
            if(self.count_op(token) == 0 or self.get_op(token) == operator):
                tokens_list[token_id] = self.tokens[token_id][0]
            else:
                if operator == ".":
                  tokens_list[token_id] =  self.canonize_simple_exp_and(token)
                elif operator == "+":
                    tokens_list[token_id] = self.canonize_simple_exp_or(token)
                else:
                    raise ValueError("Operador de create_cannon_equivalence deve ser + ou .")

    def get_canon(self, from_tokens, operator):
        self.create_canon_equivalence(from_tokens, operator)
        expr = from_tokens[list(from_tokens.keys())[-1]]
        while(expr.find("0x") != -1):
            matches = regex.findall(patterns.TOKENS, expr, regex.VERSION1)
            for token in matches:
                untokenized_exp = from_tokens[token]
                replace_exp = f"({untokenized_exp})" if self.count_op(untokenized_exp) != 0 else f"{untokenized_exp}"
                expr = expr.replace(token, replace_exp)
        return expr
    
    def canonize_simple_exp_and(self, expr):
        op = self.get_op(expr)
        matches = regex.findall(patterns.TOKENS, expr, regex.VERSION1)
        match op:
            case "+":
                return f"~(~{matches[0]}.~{matches[1]})"
            case ">":
                return f"~({matches[0]}.~{matches[1]})"
            case "=": #¬(¬A∧B)∧¬(A∧¬B) 
                return f"~(~{matches[0]}.{matches[1]}).~({matches[0]}.~{matches[1]})"
            case "^":
                return f"~(~(~{matches[0]}.{matches[1]}).~({matches[0]}.~{matches[1]}))"

        return expr
    
    def canonize_simple_exp_or(self, expr):
        op = self.get_op(expr)
        matches = regex.findall(patterns.NEGATED_TOKENS, expr, regex.VERSION1)
        match op:
            case ".":
                return f"~(~{matches[0]}+~{matches[1]})"
            case ">":
                return f"(~{matches[0]}+{matches[1]})"
            case "=": #¬(¬A∨¬B)∨¬(A∨B)
                return f"~(~{matches[0]}+~{matches[1]})+~({matches[0]}+{matches[1]})"
            case "^": #¬(A∨~B)∨¬(~A∨B)
                return f"~({matches[0]}+~{matches[1]})+~(~{matches[0]}+{matches[1]}))"
            
        return expr
    
    def recreate_exp_from_tokens(self):
        expr = self.tokens[list(self.tokens.keys())[-1]][0]
        while(expr.find("0x") != -1):
            matches = regex.findall(patterns.TOKENS, expr, regex.VERSION1)
            for token in matches:
                untokenized_exp = self.tokens[token][0]
                replace_exp = f"({untokenized_exp})" if self.count_op(untokenized_exp) != 0 else f"{untokenized_exp}"
                expr = expr.replace(token, replace_exp)
        return expr

    def simplify_tokens(self): #O uso de regex aqui vai ser intenso.... contemplem o primeiro algoritmo O(n^^2)(n tetration 2)
        for token_id in self.tokens:
            token = self.tokens[token_id][0]
            if(self.count_op(token) > 0):
                simplifiable = regex.match(patterns.CONTRADICTION, token, regex.VERSION1) #Vamos ver se da pra simplificar por contradição, vo tentar deixar os nomes dos padrões (primeiro argumento) claros pra evitar 1 trilhão de comentarios
                matches = []
                if(simplifiable):
                    matches = regex.match(patterns.TOKENS, token, regex.VERSION1)[0] #Como a expresão é A.~A(ou ~A.A) qualquer valor dentro dessa lista é o mesmo, então vamos usar o 0
                    self.tokens_simplified[token_id] = "False"
                print(simplifiable)
            
    def parse_truth_table_line(self, line):
        for i in range(self.variable_amount):
            self.tokens[self.var_to_tokens[self.variable_lists[i]]][1] = self.table[line][i]   
        rexp = self.solve_exp(self.tokens[list(self.tokens.keys())[-1]][0])
       # print(self.tokens)
        return rexp

    def create_truth_table(self):
        self.table = None #Limpa a tabela para recalcular
        for i in range(self.table_rows):
            if(self.table == None):
                self.table = [[False] * self.variable_amount]
            else:
                self.table.append([False] * self.variable_amount)
            rowBinValue = bin(i)[2:].zfill(self.variable_amount) #Gera o valor binário da linha atual, preenchendo com zeros à esquerda para garantir que tenha o mesmo número de dígitos que o número de variáveis
            for j in range(self.variable_amount):
                self.table[i][j] = rowBinValue[j] == '1'
        self.table =  self.table[::-1] #Invertendo a orientação da tabela para seguir oq a gente viu em aula, apesar de não fazer diferença
        self.table_len = len(self.table)

    def parse_truth_table(self):
        self.variable_lists.sort() #Não faria diferença aqui, PORÉM, é mais dificil de ler a tabela assim, e eu perdi uma quantidade de tempo que não me orgulho tentando arrumar um erro que não existia por causa dessa diferença
        trues = 0
        print("X - -  " ,self.variable_lists)
        for i in range(self.table_rows):
            line = self.parse_truth_table_line(i)
            trues = trues + 1 if line else trues 
            #print(tokens)
            print(f"Linha {i+1}: {self.table[i]} = Resultado: {line}")
        
        print(f"\nEssa tabela apresenta uma: {"Tauntologia" if trues == self.table_rows else "Contingência" if trues != 0 else "Contradição"}")
        print("\n[Depuração] Como a expressão foi entendida", self.recreate_exp_from_tokens())
    
    def tokenize_linear_exp(self, exp):
        for op in [ '.', '^' , '+', '>', '=']:
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
            token = final_exp
            if(token in self.var_to_tokens):
                token = self.var_to_tokens[token]
            for i in range(len(extracted)):
                extracted[i] =  extracted[i].replace("("+exp+")", token)   
    
        matches = matches.replace(outer, token)

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
        return len(regex.findall(patterns.OPERATOR, exp, regex.VERSION1))

    def find_low_complexity_exp(self, exp, op):
        matches = regex.findall(patterns.FINAL_EXPRESSION_WILDCARD.replace("*", op), exp, regex.VERSION1)
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
           # 
           # while(self.count_op(self.tokens[list(self.tokens.keys())[-1]][0]) == 0 and
               # self.tokens[list(self.tokens.keys())[-1]][0].find("~") == -1 ): 
                #self.tokens.popitem() #Caso o ultimo token seja uma expressão sem operadores E não negada, isso significa que o penultimo é a resolução real, então remove ele
        self.tokenize_linear_exp(tokenized)
        

def parse_expression_input(exp):
    exp = exp.replace(" ", "") #Remover todo e qualquer espaço, ele não possui função atualmente, e ""pode"" atrapalhar a interpretação da expressão
    """
    A.B = Padrão
    A.B : B.A = Comparação
    A.B ? B.A = Consequencia lógica
    A.B @ 1 = Resolver somente linha 1
    """
    if(exp.find(":") != -1):
        exprs = exp.split(":")
        try:
            assert(len(exprs) == 2)
            expr1 = Parser()
            expr2 = Parser() #Duas instancias, cada uma dela vai interpretar uma expressão, dps a gente compara linha por linha para ver se elas são iguais
            expr1.solve(exprs[0])
            expr2.solve(exprs[1])
            if(expr1.variable_amount != expr2.variable_amount): 
                print("[RESULTADO] As duas expressões NÃO são equivalentes, pois a primeira expressão tem", expr1.variable_amount, "proposições, e a segunda tem", expr2.variable_amount)
                return
            varList1 = expr1.variable_lists.copy()
            varList1.sort()
            varList2 = expr2.variable_lists.copy()
            varList2.sort() #Arruma as listas de variaveis pra evitar que elas não sejam iguais só por estarem em ordens diferentes
            if(varList1 != varList2):
                print("[RESULTADO] As expressões não são equivalente, pois", exprs[0], "e", exprs[1], "usam variaveis diferentes")
                return
            expr1.create_truth_table()
            expr2.create_truth_table()
            for i in range(expr1.table_len): #Elas tem a mesma quantidade de linhas
                if(expr1.parse_truth_table_line(i) != expr2.parse_truth_table_line(i)):
                    print("[RESULTADO]", exprs[0], "NÃO equivale a", exprs[1])
                    return
            print("[RESULTADO]", exprs[0], "equivale a", exprs[1])
        except AssertionError:
            print("O formato de comparação é <expressão 1> : <expressão 2>") 
    elif(exp.find("?") != -1):
        exprs = exp.split("?")
        try:
            assert(len(exprs) == 2)
            expr1 = Parser()
            expr2 = Parser()
            expr1.solve(exprs[0])
            expr2.solve(exprs[1])
            if(expr1.variable_amount != expr2.variable_amount): 
                print("[RESULTADO] Não existe relação de equivalência lógica entre as expressões, pois a primeira expressão tem", expr1.variable_amount, "proposições, e a segunda tem", expr2.variable_amount)
                return
            varList1 = expr1.variable_lists.copy()
            varList1.sort()
            varList2 = expr2.variable_lists.copy()
            varList2.sort()
            if(varList1 != varList2):
                print("[RESULTADO] Não existe relação de equivalência lógica entre as expressões, pois", exprs[0], "e", exprs[1], "usam variaveis diferentes")
                return
            expr1.create_truth_table()
            expr2.create_truth_table()
            rl = True
            lr = True
            for i in range(expr1.table_len): #Elas tem a mesma quantidade de linhas
                if(lr and not (not (expr1.parse_truth_table_line(i)) or expr2.parse_truth_table_line(i))):
                    print("[RESULTADO]", exprs[1], "NÃO é consequencia lógica de", exprs[0])
                    lr = False
                if(rl and not (not (expr2.parse_truth_table_line(i)) or expr1.parse_truth_table_line(i))):
                    print("[RESULTADO]", exprs[0], "NÃO é consequencia lógica de", exprs[1])
                    rl = False
                if(not rl and not lr): break

            if(rl) : print("[RESULTADO]", exprs[0], "é consequencia lógica de", exprs[1])
            if(lr) : print("[RESULTADO]", exprs[1], "é consequencia lógica de", exprs[0])
        except AssertionError:
            print("O formato de consequencia lógica é <expressão 1> ? <expressão 2>") 
    elif(exp.find("@") != -1):
        exprs = exp.split("@")
        try:
            assert(len(exprs) == 2)
            line = int(exprs[1]) 
            assert(line >= 0)
            expr1 = Parser()
            expr1.solve(exprs[0])
            expr1.create_truth_table()
            if(line >= expr1.table_len):
                print("O numero da linha fornecido deve ser menor que ao valor de linhas da tabela", line, " > ", expr1.table_len-1)
                return
            print(f"Linha {line}: {expr1.table[line]} = Resultado: {expr1.parse_truth_table_line(line)}")
        except ValueError:
            print("O número da linha deve ser um valor númerico e inteiro")
        except AssertionError:
            print("O formato da interpretação de linha única é <expressão 1> @ <numero da linha inteiro e positivo>") 
    else:
        expr1 = Parser()
        expr1.solve(exp)
        expr1.create_truth_table()
        expr1.parse_truth_table()
        print(expr1.tokens)
        expr1.simplify_tokens()
        print("Forma canônica E: " + expr1.get_canon(expr1.tokens_canon_and_equivalent, "."))
        print("Forma canônica OU: " + expr1.get_canon(expr1.tokens_canon_or_equivalent, "+"))
        print( "\n", expr1.tokens_canon_and_equivalent, "\n", expr1.tokens_canon_or_equivalent, "\n", expr1.tokens_simplified)
def main():
    '''
     
    '''
    inp = ""
    #parse_expression_input("~(((a)))")
    #parse_expression_input("c.((((a+b))))")
    #parse_expression_input("(p>q).(p>~q)")
    #parse_expression_input("(p.~p)")
    #parse_expression_input("False+(False+True)>False")
    while(1):
     

            print(
                "\nSimbolos disponíveis:\n"\
                "- `.` para AND\n"\
                "- `+` para OR\n"\
                "- `>` para IMPLICAÇÃO\n"\
                "- `=` para BICONDICIONAL\n"\
                '- `^` para XOR - NOTA: XOR tem precedência sobre OR nesse código, pois não consegui encontrar um consenso sobre isso\n'
                "- `~` para NEGACÃO\n"\
                "- `(` e `)` para delimitar expressões, não são obrigatórios, mas ajudam a definir a precedência das operações.\n" \
                "- Use <exp1> ? <exp2> para checar se exp1 é consequência lógica de exp2.\n"\
                "- Use <exp1> : <exp2> para checar se exp1 é equivalente a exp2.\n"\
                "- Use <exp1> @ <linha> para checar o resultado de uma única linha da tabela verdade\n"\
                "Nota: Evite utilizar nomes de váriaveis com sequências de caracteres repetidas, ex: AAAAA, BABABABA etc\n"\
                "Digite `exit` para sair\n"\
                "Favor reportar qualquer erro que encontrar.\n"
            )
            inp = input("Digite sua equação: ").replace(" ", "")
            if(inp == "exit" or inp == ""):
                return
            parse_expression_input(inp)
            input("Pressione [Enter] para continuar")

if __name__ == "__main__":
    main()