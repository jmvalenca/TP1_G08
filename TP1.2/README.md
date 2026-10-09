# TP1.2 - Sudoku genérico

Gonçalo Faria e Ângelo Fernandes - Lógica Computacional, 2026/2027.

Neste exercício implementámos um Sudoku genérico de lado `n²`. No notebook
explicamos o modelo e mostramos exemplos 4x4 e 9x9. Testámos também uma grelha
16x16 e implementámos o extra das diagonais.

## Ficheiros

- `sudoku.py`: notebook e implementação.
- `sudoku.pdf`: cópia executada do notebook.
- `test_sudoku.py`: cinco testes de resolução.
- `RELATORIO.md`: explicação curta e correspondência com o enunciado.
- `enunciado_professor.py`: enunciado original, sem alterações.

## Execução

Os comandos seguintes são executados na pasta principal do trabalho:

```bash
.venv/bin/marimo edit TP1.2/sudoku.py
.venv/bin/python -m unittest discover -s TP1.2 -v
```

Os passos para criar `.venv` estão no README principal. Os testes devem ser
executados sem `python -O`, porque a validação usa `assert`.

## Testes e resultados

Nos cinco testes resolvemos grelhas 4x4, 9x9 e 16x16, um Sudoku diagonal e
verificamos um caso com pistas impossíveis. Em cada solução conferimos todas
as linhas, colunas, blocos e pistas. No notebook verificamos ainda os limites
de `add` e os caminhos nos dois sentidos, conforme o enunciado.

`None` significa que foi provado que não há solução. Se o solver não concluir,
há uma exceção. As pistas pertencem a um grupo `AllDifferent`, como pede R5:
também têm de ter valores diferentes entre si.

## Registo de apoio

Incluímos o registo de apoio em
[`../conversas/TP1.2_assistencia.json`](../conversas/TP1.2_assistencia.json).
