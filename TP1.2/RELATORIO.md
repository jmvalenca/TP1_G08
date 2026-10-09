# TP1.2 - Sudoku genérico

Gonçalo Faria e Ângelo Fernandes - Lógica Computacional, 2026/2027.

## O problema

Para `n=3`, temos o Sudoku normal 9x9. Para outro `n`, o lado é sempre `N=n²`
e cada bloco tem `n x n` células. Temos de colocar os valores `1..N` sem
repetições nas linhas, colunas e blocos, mantendo as pistas.

Escolhemos o CP-SAT do OR-Tools, sugerido na cadeira. Assim, escrevemos as
variáveis e as regras diretamente e deixamos a procura da solução para o solver.

## Estrutura da implementação

| Requisito | Código | O que faz |
| --- | --- | --- |
| R1 | `box` | Guarda `(linha, coluna) -> valor ou None`, valida `add` e cria a matriz |
| R2 | `cube` | Escolhe as células de um bloco `n x n` |
| R3 | `path` | Escolhe um segmento horizontal ou vertical, nos dois sentidos |
| R4 | `random_clues` | Sorteia `k` posições distintas e os seus valores |
| R5 | `SudokuCSP` | Cria variáveis, aplica `AllDifferent`, fixa pistas e resolve |
| R6 | `make_sudoku` | Junta linhas, colunas, blocos e um grupo de pistas |

Separámos os grupos de células das regras do Sudoku. Uma `box` guarda as
células num dicionário, sem precisar de guardar a grelha toda. Só criamos a
matriz quando queremos mostrar o grupo; os zeros significam células livres
ou fora do grupo.

`cube` e `path` escolhem coordenadas. O modelo recebe qualquer número de
grupos e aplica sempre a mesma regra. Para `n=2`, o bloco `cube(2,1,1)` contém
`(2,2)`, `(2,3)`, `(3,2)` e `(3,3)`.

## Modelo e resultado

Criámos uma variável inteira `x[i,j]` por célula, com valores entre `1` e `N`.
Aplicamos `AllDifferent` a cada grupo e fixamos cada pista com `x[i,j]=v`.
Uma linha, coluna ou bloco tem `N` células e `N` valores possíveis. Se todos
forem diferentes, o grupo contém exatamente `1..N`. Isto explica por que o
modelo cumpre as regras do Sudoku.

`solve()` devolve a matriz para `OPTIMAL` ou `FEASIBLE`, e `None` para
`INFEASIBLE`. Se o solver não concluir, levanta um erro. Usamos um limite de
10 segundos e um trabalhador. Um limite de tempo não prova impossibilidade.

## Pistas aleatórias

Escolhemos posições sem repetição e valores independentes. Isto pode criar
um caso impossível; os exemplos tentam novas pistas até 20 vezes. A função
que sorteia pistas continua separada do solver.

Há uma particularidade do enunciado: R5 aplica `AllDifferent` a todos os
grupos, incluindo o grupo das pistas. Assim, duas pistas com o mesmo valor
são incompatíveis mesmo em linhas, colunas e blocos diferentes. Com `k>N`
pistas nesse grupo, nunca há solução. Não retiramos esta regra para imitar
um puzzle convencional, porque faz parte da interface pedida.

A nossa implementação encontra uma solução, mas não garante que seja única.

## Testes

No notebook mostramos exemplos 4x4 e 9x9. Testámos também uma grelha 16x16 e
um Sudoku diagonal 4x4. Para cada resultado, conferimos linhas, colunas,
blocos, preservação das pistas e a regra do grupo de pistas, sem consultar
o solver. Verificamos as diagonais separadamente no exemplo e no teste.

Em `test_sudoku.py` reunimos cinco testes: 4x4, 9x9, 16x16, Sudoku diagonal
e pistas impossíveis. Validamos cada solução por completo. No notebook
incluímos as duas rejeições de `add` pedidas pelo enunciado e verificamos os
caminhos no sentido inverso. Os exemplos executados estão em `sudoku.pdf`.

## Custo

Com `N=n²`, há `N²` variáveis e `3N` grupos principais de `N` células.
Construir o modelo base custa `O(N²+k)` em tempo e espaço, sem contar as
estruturas internas do solver. Se passarmos grupos extra, o custo depende
também da soma dos seus tamanhos. Validar custa `O(N²+k)`. Criar um bloco ou
linha completa custa `O(N)`; criar a matriz de uma `box` custa `O(N²)`.

A procura domina o custo. Sem cortar possibilidades, existem até `N^(N²)`
atribuições. CP-SAT reduz a procura usando as restrições, mas não tem uma
garantia polinomial geral. Os tempos do notebook pertencem a essas instâncias
e a esta máquina; não garantem o mesmo desempenho em todos os puzzles.
Testámos 16x16. O extra 36x36 do enunciado não foi demonstrado.

## Extra das diagonais

Juntamos duas `box`, uma por diagonal. Não foi preciso alterar a lógica do
solver: é a mesma regra aplicada a mais dois grupos.

## Registo de apoio

Incluímos o registo de apoio em
[`../conversas/TP1.2_assistencia.json`](../conversas/TP1.2_assistencia.json).

## Referências

- Enunciado original em `enunciado_professor.py`.
- [OR-Tools CP-SAT](https://developers.google.com/optimization/cp/cp_solver/).
- [Marimo](https://docs.marimo.io/).
