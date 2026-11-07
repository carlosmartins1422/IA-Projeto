# ALGORITMOS DE PROCURA DE REFERÊNCIA
# BFS (não informado) e A* (informado, com heurística de referência) implementados.
# Não assumir que BFS minimiza custos variáveis: apenas minimiza nº de passos.

import heapq
import math
from collections import deque

from heuristicas import heuristica_referencia


def custo_aresta(comprimento, velocidade):
    # Decisão da Fase 1: custo = ceil(comprimento / velocidade), em passos de tempo
    return math.ceil(comprimento / velocidade)


def custo_caminho(ambiente, caminho, velocidade):
    # Soma dos custos das arestas de um caminho (lista de nós).
    # Usa o grafo completo (ambiente.grafo) porque só mede o caminho, não o procura.
    total = 0
    for u, v in zip(caminho, caminho[1:]):
        total += custo_aresta(ambiente.grafo[u][v], velocidade)
    return total


def bfs(ambiente, origem, objetivo, velocidade=1):
    # Procura Primeiro em Largura (fronteira FIFO + conjunto explorado).
    # objetivo: um nó (str) ou um conjunto de nós (ex.: ambiente.saidas).
    # Devolve um dicionário: sucesso, caminho, custo, nos_explorados.
    objetivos = {objetivo} if isinstance(objetivo, str) else set(objetivo)

    def resultado(sucesso, caminho, explorados):
        custo = custo_caminho(ambiente, caminho, velocidade) if sucesso else None
        return {"sucesso": sucesso, "caminho": caminho,
                "custo": custo, "nos_explorados": explorados}

    if origem not in ambiente.grafo:
        return resultado(False, [], 0)

    # Teste do objetivo no estado inicial
    if origem in objetivos:
        return resultado(True, [origem], 0)

    fronteira = deque([origem])      # fila FIFO
    pai = {origem: None}             # guarda de onde veio cada nó (reconstrói o caminho)
    explorados = 0                   # nº de nós expandidos

    while fronteira:
        atual = fronteira.popleft()  # o mais antigo = o menos profundo
        explorados += 1

        # sorted -> desempate por identificador (regra da Fase 1)
        for vizinho in sorted(ambiente.vizinhos(atual)):
            if vizinho in pai:       # já está na fronteira ou já foi explorado
                continue
            pai[vizinho] = atual
            if vizinho in objetivos:  # teste do objetivo ao gerar o nó (como nos slides)
                caminho = []
                no = vizinho
                while no is not None:
                    caminho.append(no)
                    no = pai[no]
                caminho.reverse()
                return resultado(True, caminho, explorados)
            fronteira.append(vizinho)

    return resultado(False, [], explorados)   # fronteira vazia: sem caminho


def a_estrela(ambiente, origem, objetivo, velocidade=1, heuristica=None):
    # A*: expande sempre o nó com menor f(n) = g(n) + h(n).
    # heuristica: função h(no). Se None, usa a heurística de referência (grafo relaxado).
    # Devolve o mesmo formato do BFS (permite comparar os dois diretamente).
    objetivos = {objetivo} if isinstance(objetivo, str) else set(objetivo)

    if origem not in ambiente.grafo:
        return {"sucesso": False, "caminho": [], "custo": None, "nos_explorados": 0}

    if heuristica is None:
        heuristica = heuristica_referencia(ambiente, objetivos, velocidade)

    g = {origem: 0}                  # melhor custo conhecido desde a origem até cada nó
    pai = {origem: None}
    fronteira = [(heuristica(origem), origem)]   # fila de prioridade (heap) de (f, nó)
    fechados = set()                 # nós já expandidos
    explorados = 0

    while fronteira:
        f, atual = heapq.heappop(fronteira)   # nó com MENOR f
        if atual in fechados:        # entrada repetida/antiga na heap
            continue

        # Teste do objetivo ao SELECIONAR o nó (é isto que garante a otimalidade)
        if atual in objetivos:
            caminho = []
            no = atual
            while no is not None:
                caminho.append(no)
                no = pai[no]
            caminho.reverse()
            return {"sucesso": True, "caminho": caminho,
                    "custo": g[atual], "nos_explorados": explorados}

        fechados.add(atual)
        explorados += 1

        for vizinho, comp in sorted(ambiente.vizinhos(atual).items()):
            if vizinho in fechados:
                continue
            h = heuristica(vizinho)
            if h == math.inf:        # nunca chegará a um objetivo: não vale a pena
                continue
            novo_g = g[atual] + custo_aresta(comp, velocidade)
            if vizinho not in g or novo_g < g[vizinho]:   # caminho melhor encontrado
                g[vizinho] = novo_g
                pai[vizinho] = atual
                heapq.heappush(fronteira, (novo_g + h, vizinho))

    return {"sucesso": False, "caminho": [], "custo": None, "nos_explorados": explorados}