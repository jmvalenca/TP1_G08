# Registo de apoio: ../conversas/TP1.1_assistencia.json.
import csv
from pathlib import Path


DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex"]
PERIODOS = list(range(1, 6))


def ler_csv(pasta, nome, colunas):
    caminho = Path(pasta) / nome

    with open(caminho, encoding="utf-8-sig", newline="") as ficheiro:
        leitor = csv.DictReader(ficheiro)
        cabecalho = leitor.fieldnames or []

        if not set(colunas).issubset(cabecalho):
            raise ValueError("colunas em falta em " + nome)

        linhas = []

        for linha in leitor:
            valores = {}

            for coluna in colunas:
                if linha[coluna] is None:
                    raise ValueError("linha incompleta em " + nome)
                valores[coluna] = linha[coluna].strip()

            linhas.append(valores)

    return linhas


def ler_dados(pasta):
    # turmas
    linhas_turmas = ler_csv(pasta, "turmas.csv", ["turma"])
    turmas = []

    for linha in linhas_turmas:
        turmas.append(linha["turma"])

    if not turmas or "" in turmas or len(set(turmas)) != len(turmas):
        raise ValueError("verifica os nomes das turmas")

    # disciplinas
    colunas = [
        "disciplina",
        "professor",
        "carga_semanal",
        "duplo_periodo",
        "sala_especial",
    ]

    linhas_disciplinas = ler_csv(pasta, "disciplinas.csv", colunas)
    disciplinas = {}

    for linha in linhas_disciplinas:
        nome = linha["disciplina"]
        professor = linha["professor"]
        duplo_periodo = linha["duplo_periodo"]

        if not nome or nome in disciplinas or not professor:
            raise ValueError("verifica os nomes das disciplinas e professores")

        if duplo_periodo not in ["sim", "nao"]:
            raise ValueError("duplo_periodo tem de ser sim ou nao")

        carga = int(linha["carga_semanal"])

        if duplo_periodo == "sim":
            duracao = 2
        else:
            duracao = 1

        carga_maxima = len(DIAS) * duracao

        if carga < 0 or carga > carga_maxima or carga % duracao != 0:
            raise ValueError("carga inválida em " + nome)

        disciplinas[nome] = {
            "professor": professor,
            "carga": carga,
            "duracao": duracao,
            "especial": linha["sala_especial"],
        }

    # salas
    colunas = ["sala", "tipo", "quantidade"]
    linhas_salas = ler_csv(pasta, "salas.csv", colunas)
    salas = {}
    nomes_salas = set()

    for linha in linhas_salas:
        nome = linha["sala"]
        tipo = linha["tipo"]
        quantidade = int(linha["quantidade"])

        if not nome or nome in nomes_salas or quantidade < 0:
            raise ValueError("verifica os nomes e quantidades das salas")

        if tipo not in ["normal", "especial"]:
            raise ValueError("tipo de sala inválido")

        nomes_salas.add(nome)

        for numero in range(1, quantidade + 1):
            salas[(nome, numero)] = tipo

    # disponibilidades
    colunas = ["professor", "dia", "periodo"]
    linhas_excecoes = ler_csv(pasta, "disponibilidade_excecoes.csv", colunas)
    indisponiveis = set()

    for linha in linhas_excecoes:
        professor = linha["professor"]
        dia = linha["dia"]
        periodo = int(linha["periodo"])

        if dia not in DIAS or periodo not in PERIODOS:
            raise ValueError("dia ou período inválido nas exceções")

        indisponiveis.add((professor, dia, periodo))

    return {
        "turmas": turmas,
        "disciplinas": disciplinas,
        "salas": salas,
        "indisponiveis": indisponiveis,
    }


def sala_compativel(dados, disciplina, sala):
    if sala not in dados["salas"]:
        return False

    especial = dados["disciplinas"][disciplina]["especial"]
    tipo = dados["salas"][sala]

    if especial:
        return sala[0] == especial and tipo == "especial"

    return tipo == "normal"


def validar(dados, horario):
    erros = set()
    turmas_ocupadas = set()
    professores_ocupados = set()
    salas_ocupadas = set()
    ocorrencias = set()
    cargas = {}

    for turma, disciplina, dia, inicio, sala in horario:
        if turma not in dados["turmas"] or disciplina not in dados["disciplinas"]:
            erros.add("R2: turma ou disciplina desconhecida")
            continue

        info = dados["disciplinas"][disciplina]
        duracao = info["duracao"]
        professor = info["professor"]
        fim = inicio + duracao - 1

        if dia not in DIAS or inicio not in PERIODOS or fim > 5:
            erros.add("R4: aula fora dos tempos do dia")
            continue

        # carga semanal e aulas no mesmo dia
        chave = (turma, disciplina)
        cargas[chave] = cargas.get(chave, 0) + duracao

        ocorrencia = (turma, disciplina, dia)

        if ocorrencia in ocorrencias:
            erros.add("R3: disciplina repetida no mesmo dia")

        ocorrencias.add(ocorrencia)

        if not sala_compativel(dados, disciplina, sala):
            erros.add("R7: sala inexistente ou incompatível")

        # verificar cada tempo da aula
        for periodo in range(inicio, inicio + duracao):
            chave_turma = (turma, dia, periodo)
            chave_professor = (professor, dia, periodo)
            chave_sala = (sala, dia, periodo)

            if chave_turma in turmas_ocupadas:
                erros.add("R1: duas aulas da turma ao mesmo tempo")

            if chave_professor in professores_ocupados:
                erros.add("R5: professor com duas aulas ao mesmo tempo")

            if chave_sala in salas_ocupadas:
                erros.add("R7: duas aulas na mesma sala")

            if chave_professor in dados["indisponiveis"]:
                erros.add("R6: professor indisponível")

            turmas_ocupadas.add(chave_turma)
            professores_ocupados.add(chave_professor)
            salas_ocupadas.add(chave_sala)

    for turma in dados["turmas"]:
        for disciplina, info in dados["disciplinas"].items():
            carga_obtida = cargas.get((turma, disciplina), 0)

            if carga_obtida != info["carga"]:
                erros.add("R2: carga semanal incorreta")

    return sorted(erros)


def contar_buracos(dados, horario):
    ocupacao = {}

    for turma, disciplina, dia, inicio, sala in horario:
        info = dados["disciplinas"][disciplina]
        chave = (info["professor"], dia)
        tempos = range(inicio, inicio + info["duracao"])

        if chave not in ocupacao:
            ocupacao[chave] = set()

        ocupacao[chave].update(tempos)

    total = 0

    for tempos in ocupacao.values():
        primeiro = min(tempos)
        ultimo = max(tempos)
        total += ultimo - primeiro + 1 - len(tempos)

    return total


def comparar(antigo, novo):
    grupos = set()

    for aula in antigo + novo:
        grupos.add(aula[:2])

    mudadas = 0
    acrescentadas = 0
    removidas = 0

    for grupo in grupos:
        antes = set()
        depois = set()

        for aula in antigo:
            if aula[:2] == grupo:
                antes.add(aula[2:])

        for aula in novo:
            if aula[:2] == grupo:
                depois.add(aula[2:])

        mantidas = len(antes & depois)
        mudadas += min(len(antes), len(depois)) - mantidas
        acrescentadas += max(0, len(depois) - len(antes))
        removidas += max(0, len(antes) - len(depois))

    return {
        "mudadas": mudadas,
        "acrescentadas": acrescentadas,
        "removidas": removidas,
    }


def exigir_solucao(dados, resultado):
    horario = resultado["horario"]

    if horario is None:
        estado = resultado["estado"]
        raise RuntimeError("não foi encontrado um horário: " + estado)

    erros = validar(dados, horario)

    if erros:
        raise AssertionError("\n".join(erros))

    return horario
