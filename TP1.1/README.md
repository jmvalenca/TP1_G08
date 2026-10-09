# TP1.1 - Gerador de Horários

Lógica Computacional - Licenciatura em Ciências da Computação, Universidade do Minho

- Ângelo Fernandes, a112434
- Gonçalo Faria, a104942

Neste exercício, construímos um gerador de horários sem conflitos e com
poucos buracos para os professores. Quando mudam os recursos, procuramos
manter o máximo de aulas de H0. No notebook explicamos o modelo e
apresentamos os horários e as medições.

## Ficheiros

- `horario_escolar.py`: explicações, restrições, resolução dos horários e resultados.
- `horarios.py`: leitura dos CSV, validação e comparação dos horários.
- `testes.py`: cinco testes de resolução e adaptação dos horários.
- `RELATORIO.md`: explicação curta do trabalho e dos limites.
- `horario_escolar.pdf`: versão do notebook para leitura.
- `dados/`: exemplo com as UCs do 3.º ano, 1.º semestre, e dois grupos.
- `dados_v2/`: o mesmo exemplo, com duas indisponibilidades adicionais do Docente A.
- `dados_teste/`: teste com mais um grupo, uma UC e uma exceção de disponibilidade.
- `dados_professor/` e `dados_professor_v2/`: CSV originais do professor.

Cada pasta de dados contém os quatro CSV usados pelo programa. No exemplo
LCC, usámos nomes de UCs do curso, mas os docentes, as cargas, as salas e
as disponibilidades são fictícios. Não correspondem ao horário oficial
da UMinho.

## Executar

Usar Python 3.14 e instalar as dependências seguindo o README da pasta
principal. Depois, a partir da pasta principal:

```bash
.venv/bin/marimo edit TP1.1/horario_escolar.py
```

Para correr os testes e verificar o notebook:

```bash
.venv/bin/python TP1.1/testes.py
.venv/bin/marimo check TP1.1/horario_escolar.py
```

Não usar `python -O testes.py`, porque os testes usam `assert`.
No notebook comparamos H1 incremental e H1 de raiz três vezes, com os
dados LCC e os originais do professor. Testamos também um exemplo com
mais uma turma e uma disciplina.

O ficheiro `testes.py` tem cinco testes:

1. Gerar o horário inicial e confirmar que fica sem buracos.
2. Adaptar os dados do professor a novas disponibilidades, comparar com
   uma resolução de raiz e reutilizar H1 quando há mais disponibilidade.
3. Resolver o exemplo com mais uma turma e uma disciplina.
4. Adaptar o horário depois de retirar uma sala normal usada.
5. Adaptar o horário com um professor substituto e a sua indisponibilidade.

Em cada solução completa, verificamos as regras de turmas, cargas,
blocos, professores e salas com a função `validar`.

## Registo de apoio

Incluímos o registo de apoio em
[TP1.1_assistencia.json](../conversas/TP1.1_assistencia.json).
