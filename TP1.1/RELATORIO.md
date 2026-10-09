# TP1.1 - Gerador de horários

Ângelo Fernandes, a112434 · Gonçalo Faria, a104942

## O que o programa faz

Neste exercício, lemos as turmas, disciplinas, salas e indisponibilidades
dos CSV e construímos um horário que cumpre R1-R8. O objetivo inicial é
reduzir os buracos dos professores. Quando os recursos mudam, partimos
do horário anterior H0 e procuramos um H1 válido que mantenha o máximo
de aulas nos mesmos tempos e salas.

No notebook `horario_escolar.py` explicamos o modelo e apresentamos as
experiências, os horários e os resultados. Neste relatório resumimos as
decisões e os limites da solução. Separámos em `horarios.py` a leitura
dos CSV, a validação e a contagem de buracos e mudanças.

Nas tabelas usamos códigos `D1`, `D2`, etc. para disciplinas e `S1`, `S2`,
etc. para salas. A legenda mostra os nomes completos. Os códigos são gerados
a partir dos dados lidos; não alteram os nomes nem as restrições.

## Modelo

Usamos CP-SAT do OR-Tools. Para cada colocação possível existe uma variável
booleana `x[turma, disciplina, dia, inicio, sala]`. Se vale 1, escolhemos
essa colocação. A duração vem do CSV: uma aula simples ocupa um tempo e
um bloco duplo ocupa dois tempos consecutivos, na mesma sala.

Só criamos colocações em salas compatíveis e em tempos em que o professor
está disponível. As restantes regras são somas destas variáveis:

| Requisito | Como fica garantido |
| --- | --- |
| R1 | No máximo uma aula por turma e tempo |
| R2 | O número de blocos corresponde exatamente à carga semanal |
| R3 | No máximo um bloco da mesma disciplina por dia e turma |
| R4 | Os blocos duplos têm duração 2 e começam entre os tempos 1 e 4 |
| R5 | No máximo uma aula por professor e tempo, em todas as disciplinas |
| R6 | Não criamos colocações durante as indisponibilidades |
| R7 | Uma sala compatível por aula, sem sobreposição |
| R8 | Os dados vêm dos quatro CSV de cada conjunto |

Numeramos as salas de cada tipo. Assim, limitar a quantidade disponível
equivale a impedir duas aulas na mesma sala no mesmo tempo. Uma sala
especial só recebe as disciplinas que pedem esse tipo de sala.

Para O1, um tempo é um buraco quando está livre e há aulas do professor
antes e depois dele nesse dia. Só os tempos 2, 3 e 4 podem ser buracos.
Minimizamos a soma destes valores. Os tempos livres antes da primeira
aula e depois da última não contam.

## Adaptação do horário

Primeiro validamos H0 com os novos dados. Se continuar válido,
reutilizamos: zero mudanças já é o melhor valor possível.

Caso contrário, construímos um modelo com as novas regras. Usamos H0 como
`hint`, uma sugestão para o solver. Minimizamos as colocações antigas que
deixam de ser usadas. Não fixamos aulas, para permitir uma reorganização
quando uma mudança afeta outras turmas ou professores.

Na adaptação, `OPTIMAL` significa o mínimo de mudanças, e não o mínimo de
buracos. O modelo é reconstruído; não guardamos o estado interno do solver.
Também não garantimos que o `hint` vá ser sempre mais rápido.

Comparamos as posições de cada turma e disciplina. Mudar o dia, início ou
sala conta uma vez. Um bloco duplo continua a ser uma aula. Novas aulas e
remoções são contadas à parte. Trocar o professor não conta como deslocação,
mas os conflitos e as disponibilidades são verificados com o novo professor.
Esta comparação assume que a duração da disciplina não muda.

## Dados e experiências

Usámos os dados LCC de `dados/` e `dados_v2/` como exemplo fictício,
não como horário oficial da universidade.
`dados_teste/` acrescenta uma turma, uma disciplina e uma indisponibilidade.

Acrescentámos `dados_professor/` e `dados_professor_v2/`, com os CSV
originais do enunciado sem alterações. O notebook executa os dois fluxos
H0 → H1: o exemplo LCC e o exemplo original do professor.

Em cada fluxo resolvemos H1 incremental e de raiz três vezes, alternando
a ordem. Medimos a construção do modelo, a resolução e a extração da
solução; a leitura dos CSV e a apresentação ficam fora da medição.
Todos os horários são validados com uma função independente do solver.

Nas experiências, H0 ficou inválido nos novos dados, por isso foi
necessário reparar aulas. Com os CSV do professor, os três incrementais
mudaram 2 aulas, enquanto as três resoluções de raiz mudaram 31.
A adaptação tinha 1 buraco; de raiz tinha 0. Ambos eram válidos e `OPTIMAL`
para o seu objetivo. Nas execuções apresentadas no PDF, as medianas foram
cerca de 0,0614 s incremental e 0,1230 s de raiz.

Os tempos dependem do computador e podem variar. Os métodos também têm
objetivos diferentes: estes resultados não isolam o efeito do `hint`.
O notebook recalcula os resultados quando é executado e indica se H0 já
é válido em v2, para distinguir reutilização de reparação.

## Testes

`python testes.py` executa cinco testes com cenários completos:

1. Gerar um horário para os dados iniciais, validá-lo e confirmar zero buracos.
2. Com os CSV do professor, adaptar H0 a novas disponibilidades e comparar
   as mudanças com uma resolução de raiz. Ao aumentar a disponibilidade,
   confirmar que H1 pode ser reutilizado.
3. Resolver os CSV de `dados_teste/`, com mais uma turma e uma disciplina.
4. Retirar uma sala normal usada em H0 e encontrar outro horário válido.
5. Trocar o professor de uma disciplina por um substituto indisponível
   num tempo de H0 e encontrar outro horário válido.

Em todos os cenários, `validar` percorre o horário completo e verifica
as cargas e os conflitos de turma, disciplina, professor e sala, os
blocos e as disponibilidades. Esta validação é independente do solver.
Também confirmamos que o número de buracos devolvido coincide com a
contagem independente. Os dados vêm dos CSV, como pedido em R8.

Na leitura dos CSV, rejeitamos linhas incompletas com um `ValueError`
que identifica o ficheiro.

## Complexidade e limites

Com T turmas, D disciplinas e S salas, há no máximo `25 * T * D * S`
variáveis de aula. Para blocos duplos só há quatro inícios por dia, e as
indisponibilidades e salas incompatíveis reduzem esse número.
Construir o modelo custa `O(T * D * (S+1) + P)`, com P professores, porque
os cinco dias e os cinco tempos são constantes. Este valor inclui
percorrer as colocações nas restrições; as variáveis de buracos crescem
com P.

Resolver um CSP não tem a mesma complexidade que construí-lo: a pesquisa
pode ser exponencial no pior caso. Usamos 10 segundos por resolução,
uma semente fixa e um único trabalhador. `FEASIBLE` é uma solução válida
sem prova de ótimo; `INFEASIBLE` é a prova de que não há solução;
`UNKNOWN` não permite concluir. Nestes dois últimos casos não produzimos
um horário para apresentar como válido.

Validar E aulas custa `O(E + T * D)`, porque cada bloco ocupa no máximo dois
tempos. A comparação simples faz várias passagens pelas aulas e pode ser
quadrática no número de aulas. É suficiente para os exemplos pequenos.
Não foi feita uma experiência numa escola grande.

Os CSV permitem retirar salas da semana inteira. Não têm um campo para
fechar uma sala apenas num certo tempo. Uma carga zero é permitida;
uma carga negativa, um duplo com carga ímpar ou uma carga impossível de
distribuir pelos cinco dias é rejeitada.

## Executar

Usar Python 3.14 com Marimo e OR-Tools, conforme o README principal.
Na pasta principal, executar `.venv/bin/marimo edit TP1.1/horario_escolar.py`
e `.venv/bin/python TP1.1/testes.py`. O PDF mostra o texto e os resultados do
notebook executado; o código completo fica nos ficheiros Python.

## Registo de apoio

Incluímos o registo de apoio em `../conversas/TP1.1_assistencia.json`.

## Referências

- Enunciado do TP1.1 da disciplina.
- [OR-Tools, CP-SAT para Python](https://developers.google.com/optimization/cp/cp_solver/).
- [Marimo](https://docs.marimo.io/).
- [Biblioteca csv de Python](https://docs.python.org/3/library/csv.html).
