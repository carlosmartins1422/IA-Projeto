# HEURÍSTICAS PARA A PROCURA
# Implementada: heurística de REFERÊNCIA (grafo relaxado), usada pelo A* base.
# Por implementar (Fase 4): DUAS heurísticas próprias do grupo (candidatas: estimar
# tempo até interceção considerando velocidades; penalizar trajetos com probabilidade
# de bloqueio dinâmico). Comparar resultados mantendo o resto fixo.
# Verificar admissibilidade/consistência quando se alegar optimalidade do A*.

import heapq
import math


def custo_aresta(comprimento, velocidade):
    # Mesma regra da Fase 1 (g e h têm de usar a MESMA unidade: passos de tempo)
    return math.ceil(comprimento / velocidade)


def distancias_relaxadas(ambiente, objetivos, velocidade):
    # Dijkstra "multi-origem": parte de TODOS os objetivos ao mesmo tempo e calcula,
    # para cada nó, o custo mínimo até ao objetivo mais próximo.
    # RELAXAMENTO: usa ambiente.grafo (todas as ligações), ignorando portas fechadas
    # e barreiras ativas. Como o grafo é bidirecional, a distância objetivo->nó
    # é igual à distância nó->objetivo.
    dist = {no: math.inf for no in ambiente.grafo}
    fronteira = []
    for obj in objetivos:
        if obj in dist:
            dist[obj] = 0
            heapq.heappush(fronteira, (0, obj))

    while fronteira:
        d, no = heapq.heappop(fronteira)
        if d > dist[no]:          # entrada antiga (já encontrámos melhor): ignorar
            continue
        for vizinho, comp in ambiente.grafo[no].items():
            nova = d + custo_aresta(comp, velocidade)
            if nova < dist[vizinho]:
                dist[vizinho] = nova
                heapq.heappush(fronteira, (nova, vizinho))
    return dist


def heuristica_referencia(ambiente, objetivos, velocidade=1):
    # Devolve a função h(no). A tabela é calculada UMA vez; depois cada consulta é O(1).
    # h(no) = custo exato até ao objetivo no mapa com tudo aberto (grafo relaxado).
    if isinstance(objetivos, str):
        objetivos = {objetivos}
    tabela = distancias_relaxadas(ambiente, objetivos, velocidade)

    def h(no):
        return tabela.get(no, math.inf)
    return h