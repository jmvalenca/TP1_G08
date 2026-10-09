# TP1 - Lógica Computacional 2026/2027

Gonçalo Faria (a104942) e Ângelo Fernandes (a112434).

Neste trabalho resolvemos dois problemas com programação por restrições:
a construção e adaptação de um horário escolar e a resolução de Sudoku
genérico. Usamos o CP-SAT do OR-Tools e apresentamos os modelos, exemplos e
resultados em notebooks Marimo.

## Organização

- `TP1.1/`: implementação dos horários, dados CSV, testes, relatório e PDF.
- `TP1.2/`: implementação do Sudoku, testes, relatório e PDF.
- `conversas/`: registos de apoio dos dois exercícios.

Explicamos a modelação e as decisões no notebook de cada exercício e no
respetivo `RELATORIO.md`. Os PDFs mostram os notebooks executados. O código
completo está nos ficheiros Python.

## Execução

Usamos Python 3.14, Marimo 0.24.2 e OR-Tools 9.15.6755. As dependências
estão também indicadas no início de cada notebook.

Na pasta principal, com `uv` instalado:

```bash
uv venv --python 3.14 .venv
uv pip install --python .venv/bin/python marimo==0.24.2 ortools==9.15.6755
.venv/bin/marimo edit TP1.1/horario_escolar.py
```

Para o Sudoku:

```bash
.venv/bin/marimo edit TP1.2/sudoku.py
```

## Testes

Incluímos cinco cenários de teste em cada exercício. Nos horários verificamos
a resolução inicial e a adaptação a diferentes alterações de recursos. No
Sudoku verificamos grelhas 4x4, 9x9 e 16x16, diagonais e pistas impossíveis.
Validamos cada solução, além das verificações presentes nos notebooks.

```bash
.venv/bin/python TP1.1/testes.py
.venv/bin/python -m unittest discover -s TP1.2 -v
.venv/bin/marimo check TP1.1/horario_escolar.py
.venv/bin/marimo check TP1.2/sudoku.py
```

Usamos `assert` nos testes e na validação, por isso executamos sem `python -O`.

## PDFs

Para gerar os PDFs a partir dos notebooks:

```bash
uv pip install --python .venv/bin/python nbformat==5.11.1 'nbconvert[webpdf]==7.17.1' playwright==1.63.0
.venv/bin/python -m playwright install chromium
.venv/bin/marimo export pdf TP1.1/horario_escolar.py -o TP1.1/horario_escolar.pdf --no-rasterize-outputs --no-include-inputs
.venv/bin/marimo export pdf TP1.2/sudoku.py -o TP1.2/sudoku.pdf --no-rasterize-outputs --no-include-inputs
```

## Registos de apoio

Incluímos os registos de apoio de cada exercício:

- [TP1.1_assistencia.json](conversas/TP1.1_assistencia.json).
- [TP1.2_assistencia.json](conversas/TP1.2_assistencia.json).
