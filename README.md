# Parser de lógica propositional

Se você caiu aqui de paraquedas: é um programa em Python que lê uma expressão lógica, monta a tabela-verdade, mostra formas canônicas (só E e só OU) e ainda deixa você brincar de equivalência e consequência lógica sem fazer na mão na véspera da prova.

A ideia geral foi tokenizar a expressão (variáveis viram placeholders hex, subexpressões viram tokens), respeitar parênteses com regex recursivo (por isso não é só o `re` da biblioteca padrão) e ir quebrando a expressão pela precedência dos operadores até tudo virar algo que dá pra avaliar linha a linha na tabela. Esse código é movido a fé, então se você não acreditar que ele vá funcionar, provavelmente ele vai crashar com algo tipo "a.b". Já sabe, se der ruim, a culpa é sua

## O que foi feito (em alto nível, pq cada dia que passa, sinto que menos entendo do que foi feito aqui)

- **Parser** com operadores customizados (ver tabela abaixo), negação `~` e parênteses opcionais para forçar precedência.
- **Tabela-verdade** gerada de cima pra baixo no estilo que costuma aparecer em aula (a lista de linhas é invertida de propósito pra bater com o que a gente desenha no caderno).
- **Formas canônicas** em termos só de conjunção (E) e só de disjunção (OU), reescrevendo os outros conectivos com as identidades clássicas.
- **Modos extras no mesmo input**: comparar duas expressões (`:`), checar consequência lógica (`?`), ou inspecionar **uma** linha da tabela (`@`).

## Dependência

O projeto usa o pacote **`regex`** (extensão do `re` com recursão `(?R)` pros parênteses aninhados). Instala assim:

```bash
pip install regex
```

Python 3.7+ pq eu usei .popitem() em algum lugar do código, e parece que os Pythons mais antigos entendem esse método meio diferente do atual

## Como usar

### Modo interativo (padrão)

Só rodar o script principal:

```bash
python main.py
```

O programa mostra os símbolos, pede a equação, imprime o resultado e espera você apertar Enter pra ir de novo. Digite `exit` ou deixe vazio pra sair.

**Espaços** na expressão são removidos automaticamente já que não mudam o sentido e atrapalhariam o parser, então o programa nem discute: some tudo.

### Símbolos

| Símbolo | Significado |
|--------|-------------|
| `.` | E (AND) |
| `+` | OU (OR) |
| `^` | OU exclusivo (XOR) |
| `>` | Implicação |
| `=` | Bicondicional |
| `~` | Negação |
| `( )` | Agrupamento — não são obrigatórios |

**Atenção:** a precedência do XOR em relação ao OR foi escolhida aqui pq até circuitos elétricos eu consultei, e aparentemente ninguem consegue concordar sobre isso, então se você espera outra ordem, use parêntese e vida que segue.
(Para gerar mais caos, eu sugiro que o XOR tenha precedência ao NOT, vou fazer um baixo assinado online)

**MAIS ATENÇÃO:** evita nome de variável com monte de caractere repetido tipo `AAAAA` ou `BABABABA`, o tokenizer pode se confundir pq eu usei mais manipulação de strings do que é legalmente permitido. Letras e números simples costumam ser mais tranquilos.

### Sintaxes

- **`expressão1 : expressão2`**  verifica se as duas são **logicamente equivalentes** (mesmas variáveis, mesma coluna de resultados na tabela).
- **`expressão1 ? expressão2`**  verifica **consequência lógica** nos dois sentidos (implicação linha a linha); pode imprimir que uma implica a outra, ou as duas, ou nenhuma, conforme o caso.
- **`expressão @ n`**  mostra só a **linha `n`** da tabela (0-based internamente como no código: linha 0, 1, …). Se o número for maior que o tamanho da tabela, o programa avisa.

Se você **não** usar `:` `?` ou `@`, o fluxo padrão é: montar a tabela, imprimir cada linha com o resultado, classificar como tautologia / contingência / contradição (conforme as linhas), mostrar um trecho de depuração com a expressão “reconstruída” dos tokens, e por fim as **formas canônicas E e OU**.



## Bugs e rough edges

Se você usar parenteses não balanceados seu computador vai se auto destruir, isso é uma core feature.