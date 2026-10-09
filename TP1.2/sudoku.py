# /// script
# requires-python = ">=3.14,<3.15"
# dependencies = [
#     "marimo==0.24.2",
#     "ortools==9.15.6755",
# ]
# ///

# Registo de apoio: ../conversas/TP1.2_assistencia.json.

import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")

with app.setup:
    import random
    import marimo as mo
    from ortools.sat.python import cp_model


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # TP1.2 - Sudoku genérico

    Gonçalo Faria e Ângelo Fernandes - Lógica Computacional, 2026/2027

    Neste exercício implementámos um Sudoku genérico numa grelha
    $n^2\times n^2$. Os números vão de $1$ a
    $n^2$ e não se podem repetir nas linhas, colunas e blocos. As pistas
    ficam com o valor inicial. Usamos grupos de células para representar
    estas regras e o CP-SAT para procurar uma solução.

    Procuramos uma solução válida. O enunciado não pede solução única.
    """)
    return


@app.class_definition
class box:
    """Grupo de celulas. None significa que nao ha valor fixo."""

    def __init__(self, n, cells=None):
        if type(n) is not int or n < 1:
            raise ValueError("n tem de ser um inteiro positivo")
        self.n = n
        self.size = n * n
        self.cells = {}
        if cells is not None:
            for (i, j), value in cells.items():
                self.add(i, j, value)

    def add(self, i, j, val=None):
        if (type(i) is not int or type(j) is not int
                or not (0 <= i < self.size and 0 <= j < self.size)):
            raise ValueError("coordenadas fora da grelha")
        if val is not None and (type(val) is not int
                                or not 1 <= val <= self.size):
            raise ValueError("valor fora do intervalo [1, n²]")
        old = self.cells.get((i, j))
        if old is not None and val is not None and old != val:
            raise ValueError("a célula já tem outro valor fixo")
        # None nao apaga uma pista
        if old is None:
            self.cells[(i, j)] = val
        return self

    def matrix(self):
        result = [[0] * self.size for _ in range(self.size)]
        for (i, j), value in self.cells.items():
            if value is not None:
                result[i][j] = value
        return result


@app.class_definition
class cube(box):
    """Bloco n por n, na posicao (i, j)."""

    def __init__(self, n, i, j):
        super().__init__(n)
        if (type(i) is not int or type(j) is not int
                or not (0 <= i < n and 0 <= j < n)):
            raise ValueError("índices de bloco inválidos")
        for row in range(i * n, (i + 1) * n):
            for col in range(j * n, (j + 1) * n):
                self.add(row, col)


@app.class_definition
class path(box):
    """Linha ou coluna entre dois pontos, incluindo os extremos."""

    def __init__(self, n, inicio, fim):
        super().__init__(n)
        if (not isinstance(inicio, (tuple, list))
                or not isinstance(fim, (tuple, list))
                or len(inicio) != 2 or len(fim) != 2):
            raise ValueError("cada extremo precisa de linha e coluna")
        i0, j0 = inicio
        i1, j1 = fim
        # confirmar os extremos primeiro
        self.add(i0, j0)
        self.add(i1, j1)
        if i0 != i1 and j0 != j1:
            raise ValueError("o troço tem de ser horizontal ou vertical")
        if i0 == i1:
            step = 1 if j1 >= j0 else -1
            for j in range(j0, j1 + step, step):
                self.add(i0, j)
        else:
            step = 1 if i1 >= i0 else -1
            for i in range(i0, i1 + step, step):
                self.add(i, j0)


@app.function
def random_clues(n, k=None, rng=None):
    """Sorteia k celulas diferentes e os valores."""
    clues = box(n)
    if k is None:
        k = n
    if type(k) is not int or not 0 <= k <= clues.size**2:
        raise ValueError("k tem de estar entre 0 e n⁴")
    if rng is None:
        rng = random.Random()
    for position in rng.sample(range(clues.size**2), k):
        i, j = divmod(position, clues.size)
        clues.add(i, j, rng.randint(1, clues.size))
    return clues


@app.class_definition
class SudokuCSP:
    """Recebe grupos e aplica a mesma regra a todos."""

    def __init__(self, n):
        if type(n) is not int or n < 1:
            raise ValueError("n tem de ser um inteiro positivo")
        self.n = n
        self.size = n * n
        self.model = cp_model.CpModel()
        self.grid = [
            [self.model.new_int_var(1, self.size, f"x_{i}_{j}")
             for j in range(self.size)]
            for i in range(self.size)
        ]
        self.group_count = 0
        self.status = None
        self.solve_seconds = None
        self.branches = None

    def add_groups(self, *groups):
        for group in groups:
            if not isinstance(group, box) or group.n != self.n:
                raise ValueError("todos os grupos têm de usar o mesmo n")
            variables = [self.grid[i][j] for i, j in group.cells]
            if variables:
                self.model.add_all_different(variables)
            for (i, j), value in group.cells.items():
                if value is not None:
                    self.model.add(self.grid[i][j] == value)
            self.group_count += 1

    def solve(self, time_limit=10.0):
        """Devolve a grelha ou None se nao houver solucao."""
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_search_workers = 1
        status = solver.solve(self.model)
        self.status = solver.status_name(status)
        self.solve_seconds = solver.wall_time
        self.branches = solver.num_branches
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return [[solver.value(x) for x in row] for row in self.grid]
        if status == cp_model.INFEASIBLE:
            return None
        raise RuntimeError(f"o solver não concluiu: {self.status}")


@app.function
def make_sudoku(n, clues, extra_groups=()):
    """Junta linhas, colunas, blocos e pistas."""
    size = n * n
    groups = []
    for i in range(size):
        groups.append(path(n, (i, 0), (i, size - 1)))
        groups.append(path(n, (0, i), (size - 1, i)))
    for i in range(n):
        for j in range(n):
            groups.append(cube(n, i, j))
    groups.append(clues)
    groups.extend(extra_groups)
    problem = SudokuCSP(n)
    problem.add_groups(*groups)
    return problem


@app.function
def validate_solution(n, solution, clues):
    """Confirma a grelha sem usar o solver. Correr sem python -O."""
    size = n * n
    expected = set(range(1, size + 1))
    assert solution is not None and len(solution) == size
    assert all(len(row) == size for row in solution)
    for i in range(size):
        assert set(solution[i]) == expected, f"linha {i} inválida"
        assert {solution[j][i] for j in range(size)} == expected, f"coluna {i} inválida"
    for bi in range(n):
        for bj in range(n):
            values = {
                solution[bi * n + di][bj * n + dj]
                for di in range(n) for dj in range(n)
            }
            assert values == expected, f"bloco {(bi, bj)} inválido"
    for (i, j), value in clues.cells.items():
        if value is not None:
            assert solution[i][j] == value, f"pista {(i, j)} alterada"
    clue_values = [solution[i][j] for i, j in clues.cells]
    assert len(set(clue_values)) == len(clue_values), "grupo de pistas repetido"
    return True


@app.function
def format_grid(grid, n):
    """Mostra a grelha com separadores entre blocos."""
    size = n * n
    width = len(str(size))
    rows = []
    for i, row in enumerate(grid):
        parts = [
            " ".join(f"{value:>{width}}" for value in row[j:j + n])
            for j in range(0, size, n)
        ]
        rows.append(" | ".join(parts))
        if i % n == n - 1 and i + 1 < size:
            rows.append("-" * len(rows[-1]))
    return "\n".join(rows)


@app.function
def run_example(n, seed, max_attempts=20):
    """Tenta outras pistas se estas nao tiverem solucao."""
    rng = random.Random(seed)
    for attempt in range(1, max_attempts + 1):
        clues = random_clues(n, rng=rng)
        problem = make_sudoku(n, clues)
        solution = problem.solve()
        if solution is not None:
            validate_solution(n, solution, clues)
            return clues, solution, problem, attempt
    raise RuntimeError("não foi possível obter pistas compatíveis nas tentativas")


@app.function
def example_markdown(n, result):
    clues, solution, problem, attempt = result
    return (
        f"## Exemplo: n={n}, grelha {n*n}×{n*n}\n\n"
        f"Pistas geradas em {attempt} tentativa(s):\n\n"
        f"```text\n{format_grid(clues.matrix(), n)}\n```\n\n"
        f"Solução validada:\n\n"
        f"```text\n{format_grid(solution, n)}\n```\n\n"
        f"Grupos: {problem.group_count}; estado: `{problem.status}`; "
        f"tempo do solver: {problem.solve_seconds:.4f} s; "
        f"ramos: {problem.branches}."
    )


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Como montamos o modelo

    Usamos `box(n)` para guardar um dicionário
    `(linha, coluna) -> valor ou None`. `cube` preenche um bloco e `path` um
    segmento reto, nos dois sentidos. Na matriz, zero significa que a célula
    está fora do grupo ou ainda não tem valor fixo.

    `random_clues` escolhe posições sem repetição e valores independentes. Esses
    valores podem tornar o caso impossível. Nesse caso `solve()` devolve
    `None` e os exemplos tentam outras pistas, até 20 vezes.

    R5 pede `AllDifferent` para todos os grupos, incluindo as pistas. Por isso,
    as pistas deste grupo também têm de ter valores diferentes entre si,
    mesmo que estejam em zonas diferentes da grelha. Com mais de $n^2$ pistas
    no mesmo grupo, não há solução. O sorteio não garante solução única.

    Usamos CP-SAT porque permite escrever variáveis inteiras e `AllDifferent`
    diretamente, como nos exemplos da cadeira. `box`, `cube` e `path` só
    escolhem as células. A regra fica em `SudokuCSP.add_groups`.
    """)
    return


@app.cell
def _():
    example_2 = run_example(2, seed=2026)
    return (example_2,)


@app.cell(hide_code=True)
def _(example_2):
    mo.md(example_markdown(2, example_2))
    return


@app.cell
def _():
    example_3 = run_example(3, seed=2027)
    return (example_3,)


@app.cell(hide_code=True)
def _(example_3):
    mo.md(example_markdown(3, example_3))
    return


@app.cell
def _():
    example_4 = run_example(4, seed=2028, max_attempts=1)
    return (example_4,)


@app.cell(hide_code=True)
def _(example_4):
    _clues, _solution, problem, _attempt = example_4
    mo.md(
        "**Teste adicional de escala:** n=4, grelha 16×16 validada; "
        f"{problem.group_count} grupos; {problem.solve_seconds:.4f} s "
        f"e {problem.branches} ramos nesta execução. "
        "Este tempo não garante o mesmo desempenho noutros puzzles."
    )
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Validação e caso impossível

    `test_sudoku.py` tem cinco cenários: 4x4, 9x9, 16x16, diagonal e pistas
    impossíveis. Em cada solução conferimos linhas, colunas, blocos e pistas.

    Incluímos também as verificações pedidas pelo enunciado:
    rejeitar uma coordenada e um valor inválidos, e percorrer caminhos ao
    contrário. Um caso impossível devolve `None`. Se o tempo acabar sem
    conclusão, o programa levanta um erro.
    Não podemos chamar impossível a um caso que o solver ainda não resolveu.
    """)
    return


@app.cell
def _():
    # os dois casos invalidos de R1
    for _i, _j, _valor in [(4, 0, None), (0, 0, 5)]:
        try:
            box(2).add(_i, _j, _valor)
        except ValueError:
            pass
        else:
            raise AssertionError("era esperado ValueError")

    assert set(path(2, (0, 3), (0, 0)).cells) == {(0, j) for j in range(4)}
    assert set(path(2, (3, 0), (0, 0)).cells) == {(i, 0) for i in range(4)}

    impossible = box(2).add(0, 0, 1).add(0, 1, 1)
    impossible_model = make_sudoku(2, impossible)
    assert impossible_model.solve() is None
    assert impossible_model.status == "INFEASIBLE"
    mo.md("**Validação:** limites e caminhos corretos; as pistas contraditórias deram `INFEASIBLE`.")
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Extra: Sudoku diagonal

    Juntamos duas `box`, uma por diagonal. O solver recebe-as como recebe
    qualquer outro grupo. Não foi preciso acrescentar outra regra ao modelo.
    """)
    return


@app.cell
def _():
    diagonal_main = box(2)
    diagonal_other = box(2)
    for i in range(4):
        diagonal_main.add(i, i)
        diagonal_other.add(i, 3 - i)
    diagonal_problem = make_sudoku(2, box(2), (diagonal_main, diagonal_other))
    diagonal_solution = diagonal_problem.solve()
    assert validate_solution(2, diagonal_solution, box(2))
    assert {diagonal_solution[i][i] for i in range(4)} == set(range(1, 5))
    assert {diagonal_solution[i][3 - i] for i in range(4)} == set(range(1, 5))
    mo.md(f"```text\n{format_grid(diagonal_solution, 2)}\n```")
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Custo e limites

    Com $N=n^2$, há $N^2$ variáveis e $3N$ grupos principais, cada um com
    $N$ células. Criar as variáveis e os grupos custa $O(N^2)$ em tempo e
    espaço, sem contar o trabalho interno do solver. Uma matriz custa
    $O(N^2)$ e um bloco ou linha completos custam $O(N)$.

    Resolver é a parte mais cara. Testar todas as atribuições daria até
    $N^{N^2}$ possibilidades. CP-SAT usa restrições para cortar a procura,
    mas não há garantia de tempo polinomial. Os tempos acima são apenas
    medições destes exemplos. O teste 16x16 não garante resolver depressa
    qualquer grelha maior.

    ## Registo de apoio

    Incluímos o registo de apoio em
    `../conversas/TP1.2_assistencia.json`.
    """)
    return


if __name__ == "__main__":
    app.run()
