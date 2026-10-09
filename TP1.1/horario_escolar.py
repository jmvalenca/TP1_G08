# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "marimo==0.24.2",
#     "ortools==9.15.6755",
# ]
# ///

# Registo de apoio: ../conversas/TP1.1_assistencia.json.
import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")

with app.setup:
    from pathlib import Path
    from statistics import median
    from time import perf_counter

    import marimo as mo
    from ortools.sat.python import cp_model

    from horarios import (
        DIAS,
        PERIODOS,
        comparar,
        contar_buracos,
        exigir_solucao,
        ler_dados,
        sala_compativel,
        validar,
    )

    PASTA = Path(__file__).resolve().parent


@app.cell(hide_code=True)
def _():
    # manter as tabelas inteiras no PDF
    mo.Html("""
    <style>
    @media print {
        table { width: 100% !important; break-inside: avoid; }
        h2, h3, h4 { break-after: avoid; }
    }
    </style>
    """)
    return


@app.cell
def _():
    mo.md(r"""
    # TP1.1 - Gerador de horários

    Lógica Computacional - LCC, Universidade do Minho

    Ângelo Fernandes - a112434

    Gonçalo Faria - a104942

    ## 1. Objetivo

    Neste exercício, construímos um horário sem conflitos, com as cargas
    certas e poucos buracos para os professores. Depois, ajustamos H0
    quando mudam os recursos.

    Usamos CP-SAT do OR-Tools, sugerido no enunciado. Cada variável indica
    se uma aula fica numa certa posição. Lemos os CSV com `csv.DictReader`:
    são tabelas pequenas e não precisamos de pandas.

    Definimos o modelo em `resolver` e separámos a leitura e a validação
    dos dados e horários em `horarios.py`.

    ## 2. Dados

    `dados/` tem um exemplo com UCs de LCC e dois grupos. Os docentes,
    cargas, salas e disponibilidades são fictícios. Não é o horário da UMinho.
    `dados_professor/` e `dados_professor_v2/` guardam os CSV originais
    do professor, sem alterações.

    Cada conjunto tem `turmas.csv`, `disciplinas.csv`, `salas.csv` e
    `disponibilidade_excecoes.csv`. A semana tem cinco dias e cinco tempos
    por dia, como no enunciado.

    O currículo é comum a todas as turmas. Uma carga de 4 representa quatro
    aulas simples ou dois blocos duplos, em dias diferentes. Rejeitamos cargas
    negativas, ímpares em blocos duplos ou que excedam um bloco por dia
    nos cinco dias. Uma carga de zero não gera aulas.

    Os CSV indicam tipos e quantidades de salas. Numeramos cada unidade:
    `("Sala de aula", 1)`, `("Sala de aula", 2)`, etc. A numeração é mantida
    entre conjuntos; reduzir a quantidade retira as salas de maior número.
    Uma disciplina sem sala especial pode usar qualquer sala de tipo `normal`.

    Representamos uma aula por `(turma, disciplina, dia, inicio, sala)`.
    A duração vem do currículo: um bloco duplo é uma entrada com dois
    tempos consecutivos na mesma sala.
    """)
    return


@app.cell
def _():
    mo.md(r"""
    ## 3. Validação e mudanças

    A função `validar` verifica, sem usar as variáveis do solver,
    as cargas, repetições no mesmo dia, duração dos blocos,
    disponibilidades, tipos de sala e conflitos de turma, professor e sala.

    Testamos R8 com os conjuntos de CSV descritos na secção 5.

    Comparamos as aulas por turma e disciplina. Mudar o dia, início ou sala
    conta como uma deslocação, mesmo num bloco duplo. Trocar apenas o professor
    não conta. As aulas acrescentadas ou removidas são contadas separadamente.

    Para os conjuntos de posições antigas `A` e novas `B`, contamos
    `min(len(A), len(B)) - len(A & B)` mudanças, evitando contar duas vezes
    a mesma deslocação. Assumimos que a duração das disciplinas não muda.
    """)
    return


@app.cell
def _():
    mo.md(r"""
    ## 4. Modelo

    Cada posição possível tem uma variável booleana
    `x[turma, disciplina, dia, inicio, sala]`, que vale 1 quando é escolhida.
    Só consideramos salas compatíveis e professores disponíveis durante
    todo o bloco.

    | Regra | Aplicação |
    | --- | --- |
    | R1 | Cada turma tem no máximo uma aula por tempo |
    | R2 | Número de blocos igual à carga semanal dividida pela duração |
    | R3 | Cada turma tem no máximo um bloco da mesma disciplina por dia |
    | R4 | Blocos duplos com dois tempos consecutivos, começando entre 1 e 4 |
    | R5 | Cada professor dá no máximo uma aula por tempo, contando todas as suas disciplinas |
    | R6 | Não criamos posições com indisponibilidades do professor |
    | R7 | Cada aula usa uma sala compatível, com no máximo uma aula por tempo |
    | R8 | As cargas, turmas, disciplinas e recursos são lidos dos CSV |

    ### Buracos (O1)

    Um buraco é um tempo livre entre aulas do mesmo professor no mesmo dia.
    Nos tempos 2, 3 e 4, usamos a relação:

    `buraco = antes E depois E NÃO ocupado`

    `antes` e `depois` indicam se existem aulas antes e depois desse tempo.
    As quatro desigualdades no código garantem a equivalência. Minimizamos
    a soma dos buracos, excluindo os tempos antes da primeira aula e depois
    da última. Uma indisponibilidade entre aulas conta como buraco.

    ### Adaptação (R9)

    Validamos H0 com os novos dados. Se for válido, é reutilizado sem mudanças.
    Caso contrário, criamos um novo modelo com H0 como `hint`: uma sugestão
    que o solver pode alterar.

    Minimizamos as posições antigas que deixam de ser usadas. As remoções
    obrigatórias têm valor fixo, pelo que também minimizamos as mudanças
    das aulas que se mantêm. Nenhuma aula fica fixa, permitindo reorganizações.
    Reutilizamos o horário, mas não o estado interno do solver.

    H0 e H1 de raiz minimizam buracos. A adaptação minimiza mudanças, como
    permitido em R9, sem variáveis auxiliares para os buracos. Estes são
    contados no final para comparação.

    Cada resolução tem um limite de 10 segundos, semente aleatória 0 e
    pesquisa sem paralelismo. `OPTIMAL` indica que o objetivo foi provado
    ótimo; `FEASIBLE` indica uma solução válida sem essa prova.
    `INFEASIBLE` indica que não existe solução. `UNKNOWN` indica ausência
    de conclusão, por exemplo quando o tempo termina sem encontrar solução.
    Os dois últimos estados não produzem horários válidos.
    """)
    return


@app.function
def resolver(dados, anterior=None, limite=10.0, semente=0):
    comeco = perf_counter()

    # H0 valido, nao precisamos de mudar aulas
    if anterior is not None and not validar(dados, anterior):
        return {
            "horario": list(anterior),
            "estado": "REUTILIZADO",
            "tempo": perf_counter() - comeco,
            "tempo_solver": 0.0,
            "buracos": contar_buracos(dados, anterior),
            "objetivo": 0,
            "limite_inferior": 0,
            "variaveis": 0,
        }

    modelo = cp_model.CpModel()
    x = {}

    por_turma = {}
    por_professor = {}
    por_sala = {}
    por_disciplina = {}
    por_dia = {}

    # posicoes possiveis de cada aula
    for turma in dados["turmas"]:
        for disciplina, info in dados["disciplinas"].items():
            professor = info["professor"]
            duracao = info["duracao"]
            chave_disciplina = (turma, disciplina)

            por_disciplina[chave_disciplina] = []

            for dia in DIAS:
                chave_dia = (turma, disciplina, dia)
                por_dia[chave_dia] = []

                for inicio in range(1, 7 - duracao):
                    tempos = range(inicio, inicio + duracao)
                    disponivel = True

                    for periodo in tempos:
                        if (professor, dia, periodo) in dados["indisponiveis"]:
                            disponivel = False
                            break

                    if not disponivel:
                        continue

                    for sala in dados["salas"]:
                        if not sala_compativel(dados, disciplina, sala):
                            continue

                        chave = (turma, disciplina, dia, inicio, sala)
                        nome = "aula_" + str(len(x))
                        variavel = modelo.new_bool_var(nome)

                        x[chave] = variavel
                        por_disciplina[chave_disciplina].append(variavel)
                        por_dia[chave_dia].append(variavel)

                        for periodo in tempos:
                            chave_turma = (turma, dia, periodo)
                            chave_professor = (professor, dia, periodo)
                            chave_sala = (sala, dia, periodo)

                            por_turma.setdefault(chave_turma, []).append(variavel)
                            por_professor.setdefault(chave_professor, []).append(
                                variavel
                            )
                            por_sala.setdefault(chave_sala, []).append(variavel)

    # R1, R5 e R7: uma aula por turma, professor e sala em cada tempo
    for grupos in [por_turma, por_professor, por_sala]:
        for variaveis in grupos.values():
            modelo.add(sum(variaveis) <= 1)

    # R2: cumprir a carga semanal
    for chave, variaveis in por_disciplina.items():
        turma, disciplina = chave
        info = dados["disciplinas"][disciplina]
        numero_blocos = info["carga"] // info["duracao"]

        modelo.add(sum(variaveis) == numero_blocos)

    # R3: uma aula da disciplina por dia
    for variaveis in por_dia.values():
        modelo.add(sum(variaveis) <= 1)

    # R4 e R6: garantidas nas posicoes que criamos
    buracos = []

    if anterior is None:
        professores = set()

        for info in dados["disciplinas"].values():
            professores.add(info["professor"])

        for professor in sorted(professores):
            for dia in DIAS:
                ocupado = {}

                for periodo in PERIODOS:
                    chave = (professor, dia, periodo)
                    aulas = por_professor.get(chave, [])
                    ocupado[periodo] = modelo.new_bool_var("ocupado")

                    modelo.add(ocupado[periodo] == sum(aulas))

                for periodo in [2, 3, 4]:
                    antes = modelo.new_bool_var("antes")
                    depois = modelo.new_bool_var("depois")
                    buraco = modelo.new_bool_var("buraco")

                    tempos_antes = []
                    tempos_depois = []

                    for outro_periodo in PERIODOS:
                        if outro_periodo < periodo:
                            tempos_antes.append(ocupado[outro_periodo])
                        elif outro_periodo > periodo:
                            tempos_depois.append(ocupado[outro_periodo])

                    modelo.add_max_equality(antes, tempos_antes)
                    modelo.add_max_equality(depois, tempos_depois)

                    # livre, mas com aulas antes e depois
                    modelo.add(buraco <= antes)
                    modelo.add(buraco <= depois)
                    modelo.add(buraco <= 1 - ocupado[periodo])
                    modelo.add(buraco >= antes + depois - ocupado[periodo] - 1)

                    buracos.append(buraco)

    # minimizar buracos ou mudancas
    if anterior is None:
        modelo.minimize(sum(buracos))
    else:
        antigas = set(anterior)
        mantidas = []

        for aula in antigas:
            if aula in x:
                mantidas.append(x[aula])

        perdidas = len(antigas) - sum(mantidas)
        modelo.minimize(perdidas)

        for chave, variavel in x.items():
            valor_anterior = int(chave in antigas)
            modelo.add_hint(variavel, valor_anterior)

    # correr o solver
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = limite
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = semente

    estado = solver.solve(modelo)
    horario = None
    total_buracos = None
    objetivo = None

    if estado in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        horario = []

        for chave, variavel in x.items():
            if solver.value(variavel):
                horario.append(chave)

    tempo_total = perf_counter() - comeco

    if horario is not None:
        total_buracos = contar_buracos(dados, horario)
        objetivo = solver.objective_value

    return {
        "horario": horario,
        "estado": solver.status_name(estado),
        "tempo": tempo_total,
        "tempo_solver": solver.wall_time,
        "buracos": total_buracos,
        "objetivo": objetivo,
        "limite_inferior": solver.best_objective_bound,
        "variaveis": len(x),
    }


@app.cell
def _():
    mo.md(r"""
    ## 5. Comparação

    Geramos H0 com `dados/` e resolvemos `dados_v2/` a partir de H0 e de raiz.
    Repetimos cada método três vezes, alternando a ordem. Em v2, o Docente A
    (Cálculo de Programas) fica indisponível nos tempos 4 e 5 de sexta-feira.
    O Docente E (Lógica Computacional) mantém a disponibilidade apenas nos
    dois últimos tempos de cada dia.

    Em `dados_teste/` acrescentamos a turma LCC3-TP3 e a UC Programação
    Concorrente, com um tempo. O Docente F está indisponível no primeiro
    tempo de segunda-feira. Testamos assim uma turma e uma disciplina novas,
    com dados lidos dos CSV e a partir de H0.

    Medimos a construção do modelo, a resolução e a extração do horário,
    incluindo a validação inicial de H0 na adaptação. A leitura dos CSV
    e a apresentação dos resultados ficam fora da medição.

    Apresentamos as três repetições e comparamos as medianas dos tempos,
    sempre com o mesmo problema e H0. Como os métodos têm objetivos diferentes,
    a diferença de tempo não depende apenas do `hint`. Os tempos também
    dependem do computador utilizado.

    Repetimos o fluxo com `dados_professor/` e `dados_professor_v2/`, que são
    os exemplos originais do enunciado. Mostramos se H0 já serve para v2:
    reutilizar um horário válido é diferente de reparar um horário inválido.
    """)
    return


@app.function
def tabela_markdown(cabecalho, linhas):
    texto = "| " + " | ".join(cabecalho) + " |\n"
    separador = ["---"] * len(cabecalho)
    texto += "| " + " | ".join(separador) + " |\n"

    for linha in linhas:
        valores = []

        for valor in linha:
            valores.append(str(valor))

        texto += "| " + " | ".join(valores) + " |\n"

    return texto


@app.function
def tabela_horario(dados, horario, turma, codigos_disciplinas, codigos_salas):
    linhas = []

    for periodo in PERIODOS:
        linha = [periodo]

        for dia in DIAS:
            texto = "-"

            for aula in horario:
                turma_aula, disciplina, dia_aula, inicio, sala = aula
                duracao = dados["disciplinas"][disciplina]["duracao"]
                fim = inicio + duracao

                mesma_turma = turma_aula == turma
                mesmo_dia = dia_aula == dia
                ocupa_periodo = inicio <= periodo < fim

                if mesma_turma and mesmo_dia and ocupa_periodo:
                    texto = codigos_disciplinas[disciplina] + "<br>" + codigos_salas[sala]

            linha.append(texto)

        linhas.append(linha)

    return tabela_markdown(["Tempo"] + DIAS, linhas)


@app.function
def tabela_professores(dados, horario):
    professores = set()

    for disciplina in dados["disciplinas"].values():
        professores.add(disciplina["professor"])

    linhas = []

    for professor in sorted(professores):
        aulas_professor = []

        for aula in horario:
            disciplina = dados["disciplinas"][aula[1]]

            if disciplina["professor"] == professor:
                aulas_professor.append(aula)

        linha = [professor]

        for dia in DIAS:
            periodos = []

            for aula in aulas_professor:
                _, nome_disciplina, dia_aula, inicio, _ = aula

                if dia_aula != dia:
                    continue

                duracao = dados["disciplinas"][nome_disciplina]["duracao"]

                for periodo in range(inicio, inicio + duracao):
                    periodos.append(periodo)

            periodos_texto = []

            for periodo in sorted(periodos):
                periodos_texto.append(str(periodo))

            if periodos_texto:
                linha.append(", ".join(periodos_texto))
            else:
                linha.append("-")

        linha.append(contar_buracos(dados, aulas_professor))
        linhas.append(linha)

    cabecalho = ["Professor"] + DIAS + ["Buracos"]
    return tabela_markdown(cabecalho, linhas)


@app.function
def executar_experiencia(
    pasta, pasta_inicial="dados", pasta_nova="dados_v2", pasta_extra="dados_teste"
):
    dados = ler_dados(pasta / pasta_inicial)
    novos = ler_dados(pasta / pasta_nova)

    inicial = resolver(dados)
    h0 = exigir_solucao(dados, inicial)

    incrementais = []
    de_raiz = []

    # alternar a ordem das execucoes
    for repeticao in range(3):
        if repeticao % 2 == 0:
            incremental = resolver(novos, h0)
            novo_horario = resolver(novos)
        else:
            novo_horario = resolver(novos)
            incremental = resolver(novos, h0)

        exigir_solucao(novos, incremental)
        exigir_solucao(novos, novo_horario)

        incrementais.append(incremental)
        de_raiz.append(novo_horario)

    teste = None

    if pasta_extra is not None:
        extra = ler_dados(pasta / pasta_extra)
        teste = resolver(extra, h0)
        exigir_solucao(extra, teste)

    return {
        "inicial": inicial,
        "incrementais": incrementais,
        "de_raiz": de_raiz,
        "teste": teste,
        "h0_valido_em_v2": not validar(novos, h0),
    }


@app.function
def texto_resultados(dados, novos, extra, experiencia):
    inicial = experiencia["inicial"]
    h0 = inicial["horario"]

    linhas = [
        [
            "H0",
            inicial["estado"],
            f'{inicial["tempo"]:.4f}',
            inicial["buracos"],
            "-",
            "-",
        ]
    ]

    grupos = [
        ("H1 incremental", experiencia["incrementais"]),
        ("H1 de raiz", experiencia["de_raiz"]),
    ]

    for nome, resultados in grupos:
        for numero, resultado in enumerate(resultados, 1):
            diferencas = comparar(h0, resultado["horario"])

            linha = [
                f"{nome} ({numero})",
                resultado["estado"],
                f'{resultado["tempo"]:.4f}',
                resultado["buracos"],
                diferencas["mudadas"],
                diferencas["acrescentadas"],
            ]
            linhas.append(linha)

    teste = experiencia["teste"]

    if teste is not None:
        diferencas = comparar(h0, teste["horario"])
        linha_teste = [
            "Teste adicional",
            teste["estado"],
            f'{teste["tempo"]:.4f}',
            teste["buracos"],
            diferencas["mudadas"],
            diferencas["acrescentadas"],
        ]
        linhas.append(linha_teste)

    cabecalho = [
        "Horário",
        "Estado",
        "Tempo (s)",
        "Buracos",
        "Mudadas",
        "Novas",
    ]
    texto = tabela_markdown(cabecalho, linhas)

    if experiencia["h0_valido_em_v2"]:
        texto += "\nH0 já é válido em v2: a adaptação reutiliza-o.\n"
    else:
        texto += "\nH0 é inválido em v2: a adaptação tem de mudar aulas.\n"

    tempos_incrementais = []
    tempos_de_raiz = []

    for resultado in experiencia["incrementais"]:
        tempos_incrementais.append(resultado["tempo"])

    for resultado in experiencia["de_raiz"]:
        tempos_de_raiz.append(resultado["tempo"])

    tempo_incremental = median(tempos_incrementais)
    tempo_de_raiz = median(tempos_de_raiz)

    primeiro_incremental = experiencia["incrementais"][0]
    primeiro_de_raiz = experiencia["de_raiz"][0]

    mudancas_incrementais = comparar(h0, primeiro_incremental["horario"])
    mudancas_de_raiz = comparar(h0, primeiro_de_raiz["horario"])

    texto += "\nMediana das 3 execuções\n\n"
    texto += f"- incremental: {tempo_incremental:.4f} s\n"
    texto += f"- de raiz: {tempo_de_raiz:.4f} s\n"

    texto += "\nAulas mudadas na primeira execução\n\n"
    texto += f'- incremental: {mudancas_incrementais["mudadas"]}\n'
    texto += f'- de raiz: {mudancas_de_raiz["mudadas"]}\n'

    if tempo_incremental < tempo_de_raiz:
        texto += "\nA adaptação foi mais rápida neste teste."
    elif tempo_incremental > tempo_de_raiz:
        texto += "\nA adaptação demorou mais neste teste."
    else:
        texto += "\nOs tempos foram iguais neste teste."

    if primeiro_incremental["estado"] == "REUTILIZADO":
        texto += (
            "\n\nH0 já cumpria os novos dados e foi reutilizado. "
            "Não foi necessário executar o solver."
        )

    texto += "\n\nTodos os horários passaram a validação."

    return texto


@app.function
def texto_horarios(dados, novos, extra, experiencia):
    horarios = [
        ("H0", dados, experiencia["inicial"]),
        ("H1 incremental", novos, experiencia["incrementais"][0]),
        ("H1 de raiz", novos, experiencia["de_raiz"][0]),
    ]

    if experiencia["teste"] is not None:
        horarios.append(("Teste adicional", extra, experiencia["teste"]))

    # nomes curtos para as tabelas caberem no PDF
    codigos_disciplinas = {}
    codigos_salas = {}
    for _, entrada, _ in horarios:
        for disciplina in entrada["disciplinas"]:
            if disciplina not in codigos_disciplinas:
                codigos_disciplinas[disciplina] = "D" + str(len(codigos_disciplinas) + 1)
        for sala in entrada["salas"]:
            if sala not in codigos_salas:
                codigos_salas[sala] = "S" + str(len(codigos_salas) + 1)

    texto = "### Legenda das tabelas\n\n"
    linhas = [[codigo, nome] for nome, codigo in codigos_disciplinas.items()]
    texto += tabela_markdown(["Código", "Disciplina"], linhas)
    texto += "\n"
    linhas = [[codigo, sala[0] + " " + str(sala[1])]
              for sala, codigo in codigos_salas.items()]
    texto += tabela_markdown(["Código", "Sala"], linhas)

    for nome, entrada, resultado in horarios:
        horario = resultado["horario"]
        texto += "\n### " + nome + "\n\n"

        for turma in entrada["turmas"]:
            texto += "\n#### Turma " + turma + "\n\n"
            texto += tabela_horario(
                entrada, horario, turma, codigos_disciplinas, codigos_salas
            )

        texto += "\n#### Professores\n\n"
        texto += tabela_professores(entrada, horario)

    return texto


@app.cell
def _():
    dados_iniciais = ler_dados(PASTA / "dados")
    dados_novos = ler_dados(PASTA / "dados_v2")
    dados_adicionais = ler_dados(PASTA / "dados_teste")

    experiencia = executar_experiencia(PASTA)

    return dados_adicionais, dados_iniciais, dados_novos, experiencia


@app.cell
def _(dados_adicionais, dados_iniciais, dados_novos, experiencia):
    resultados_md = texto_resultados(
        dados_iniciais,
        dados_novos,
        dados_adicionais,
        experiencia,
    )

    mo.md("## 6. Resultados\n\n" + resultados_md)
    return (resultados_md,)


@app.cell
def _(dados_adicionais, dados_iniciais, dados_novos, experiencia):
    horarios_md = texto_horarios(
        dados_iniciais,
        dados_novos,
        dados_adicionais,
        experiencia,
    )

    mo.md("## 7. Horários\n\n" + horarios_md)
    return (horarios_md,)


@app.cell
def _():
    dados_professor = ler_dados(PASTA / "dados_professor")
    dados_professor_novos = ler_dados(PASTA / "dados_professor_v2")
    experiencia_professor = executar_experiencia(
        PASTA, "dados_professor", "dados_professor_v2", None
    )

    return dados_professor, dados_professor_novos, experiencia_professor


@app.cell
def _(dados_professor, dados_professor_novos, experiencia_professor):
    professor_resultados_md = texto_resultados(
        dados_professor, dados_professor_novos, None, experiencia_professor
    )
    mo.md("## 8. Dados originais do professor\n\n" + professor_resultados_md)
    return (professor_resultados_md,)


@app.cell
def _(dados_professor, dados_professor_novos, experiencia_professor):
    professor_horarios_md = texto_horarios(
        dados_professor, dados_professor_novos, None, experiencia_professor
    )
    mo.md(professor_horarios_md)
    return (professor_horarios_md,)


@app.cell
def _():
    mo.md(r"""
    ## 9. Testes

    Em `testes.py`, usamos `resolver` do notebook e as funções de apoio de
    `horarios.py` para verificar cinco cenários: horário inicial sem buracos,
    alteração de disponibilidades nos CSV do professor, mais uma turma
    e disciplina, redução de salas e substituição de professor.
    No teste de disponibilidades, comparamos H1 com uma resolução de raiz
    e confirmamos a reutilização quando há mais disponibilidade.
    Em todos os casos, verificamos a solução completa com `validar`,
    sem usar as variáveis do solver, e contamos os buracos à parte.

    ## 10. Complexidade e limites

    Com T turmas, D disciplinas e S salas, criamos no máximo
    `25 * T * D * S` variáveis de aula. As restrições percorrem essas
    posições, mais as variáveis de buracos de cada professor.
    Construir o modelo é polinomial; encontrar o melhor horário pode
    exigir uma pesquisa exponencial. O limite de tempo evita esperar
    indefinidamente, mas pode terminar sem provar o ótimo.

    Um horário de raiz pode ter poucos buracos e diferir muito de H0.
    Na adaptação, `OPTIMAL` refere-se a minimizar mudanças, não buracos.

    Os novos CSV permitem alterar disponibilidades, quantidades de salas
    e professores, ou acrescentar turmas. Identificamos cada aula pela turma
    e disciplina e consultamos o professor nos novos dados. Aceitamos
    quantidades de salas iguais a zero, embora possam impedir uma solução.

    Reduzir a quantidade no CSV retira salas durante toda a semana;
    o formato não permite fechos apenas em certos tempos. Alterar o nome
    do tipo de sala conta como mudança de sala.

    O modelo cresce com o número de turmas, disciplinas, tempos e salas.
    Os conjuntos testados são pequenos e não permitem avaliar o desempenho
    numa escola grande. O `hint` não garante uma adaptação mais rápida.

    ## 11. Execução

    Com o ambiente instalado, executamos
    `.venv/bin/marimo edit TP1.1/horario_escolar.py` na pasta principal,
    mantendo `horarios.py` junto do notebook.
    As células leem os CSV e apresentam os horários e a comparação.
    `.venv/bin/python TP1.1/testes.py` executa os testes no terminal.

    ## 12. Registo de apoio

    Incluímos o registo de apoio em `../conversas/TP1.1_assistencia.json`.

    ## Referências

    - Enunciado TP1.1 da disciplina
    - [OR-Tools: CP-SAT para Python](https://developers.google.com/optimization/cp/cp_solver/)
    - [Marimo](https://docs.marimo.io/)
    - [Python: csv](https://docs.python.org/3/library/csv.html)
    """)
    return


if __name__ == "__main__":
    app.run()
