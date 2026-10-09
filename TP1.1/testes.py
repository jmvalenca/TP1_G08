"""Cinco testes do TP1.1. Executar: python testes.py (sem -O)."""

# Registo de apoio: ../conversas/TP1.1_assistencia.json.

from copy import deepcopy
from pathlib import Path

from horario_escolar import resolver
from horarios import comparar, contar_buracos, ler_dados, validar

PASTA = Path(__file__).resolve().parent


def horario_validado(dados, resultado):
    horario = resultado["horario"]
    assert horario is not None, resultado["estado"]
    erros = validar(dados, horario)
    assert not erros, "\n".join(erros)
    assert resultado["buracos"] == contar_buracos(dados, horario)
    return horario


def teste_inicial(dados, h0, resultado):
    # exemplo inicial sem buracos
    horario_validado(dados, resultado)
    assert resultado["estado"] == "OPTIMAL"
    assert resultado["objetivo"] == 0
    assert contar_buracos(dados, h0) == 0


def teste_disponibilidade(dados, h0, resultado):
    antigos = ler_dados(PASTA / "dados_professor")
    novos = ler_dados(PASTA / "dados_professor_v2")
    h_inicial = horario_validado(antigos, resolver(antigos))
    assert validar(novos, h_inicial), "H0 devia precisar de alterações"

    adaptado = resolver(novos, h_inicial)
    h1 = horario_validado(novos, adaptado)
    h_raiz = horario_validado(novos, resolver(novos))
    diferencas = comparar(h_inicial, h1)
    perdidas = diferencas["mudadas"] + diferencas["removidas"]
    assert adaptado["objetivo"] == perdidas
    assert diferencas["mudadas"] <= comparar(h_inicial, h_raiz)["mudadas"]

    # mais disponibilidade, podemos manter H1
    livres = deepcopy(novos)
    livres["indisponiveis"] = set()
    reutilizado = resolver(livres, h1)
    horario_validado(livres, reutilizado)
    assert reutilizado["estado"] == "REUTILIZADO"
    assert reutilizado["horario"] == h1


def teste_mais_turmas(dados, h0, resultado):
    novos = ler_dados(PASTA / "dados_teste")
    assert len(novos["turmas"]) > len(dados["turmas"])
    assert len(novos["disciplinas"]) > len(dados["disciplinas"])
    h1 = horario_validado(novos, resolver(novos, h0))
    assert comparar(h0, h1)["acrescentadas"] > 0


def teste_menos_salas(dados, h0, resultado):
    novos = deepcopy(dados)

    # tirar uma sala normal usada em H0
    sala = next(aula[4] for aula in h0 if dados["salas"][aula[4]] == "normal")
    del novos["salas"][sala]
    h1 = horario_validado(novos, resolver(novos, h0))
    assert all(aula[4] != sala for aula in h1)
    assert comparar(h0, h1)["mudadas"] > 0


def teste_substituir_professor(dados, h0, resultado):
    novos = deepcopy(dados)
    turma, disciplina, dia, inicio, sala = h0[0]
    substituto = novos["disciplinas"][disciplina]["professor"] + " (substituto)"
    novos["disciplinas"][disciplina]["professor"] = substituto
    novos["indisponiveis"].add((substituto, dia, inicio))

    # substituto indisponivel no tempo antigo
    assert validar(novos, h0)
    h1 = horario_validado(novos, resolver(novos, h0))
    assert comparar(h0, h1)["mudadas"] > 0


def executar_testes():
    dados = ler_dados(PASTA / "dados")
    resultado = resolver(dados)
    h0 = horario_validado(dados, resultado)
    testes = [
        ("horário inicial e buracos", teste_inicial),
        ("perda e ganho de disponibilidade", teste_disponibilidade),
        ("mais turmas e disciplinas", teste_mais_turmas),
        ("menos salas disponíveis", teste_menos_salas),
        ("substituição de professor", teste_substituir_professor),
    ]

    for nome, teste in testes:
        teste(dados, h0, resultado)
        print("OK - " + nome)

    print(f"\n{len(testes)} testes passaram.")


if __name__ == "__main__":
    executar_testes()
