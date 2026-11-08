# DECISÕES DOS DRONES
# Implementada: perseguição direta (estratégia de REFERÊNCIA): cada drone persegue o
# intruso conhecido que lhe fica mais próximo, sem coordenação entre drones.
# Por implementar (Fase 4): estratégia ORIGINAL do grupo: cooperar/atribuir alvos,
# protegendo uma saída ou antecipando a interceção, em vez de todos perseguirem o mesmo.

from collections import deque

from procura import a_estrela


def saltos_ate(ambiente, origem, maximo):
    # BFS limitada: devolve {nó: nº de saltos} para todos os nós a <= 'maximo' saltos.
    # Usa só ligações abertas (porta fechada/barreira ativa bloqueiam a deteção).
    saltos = {origem: 0}
    fila = deque([origem])
    while fila:
        no = fila.popleft()
        if saltos[no] == maximo:      # já no limite: não alargar mais
            continue
        for vizinho in ambiente.vizinhos(no):
            if vizinho not in saltos:
                saltos[vizinho] = saltos[no] + 1
                fila.append(vizinho)
    return saltos


class PerseguicaoDireta:
    def __init__(self):
        # Conhecimento PARTILHADO: id do intruso -> última posição conhecida.
        # (Decisão da Fase 1: se um drone deteta, todos ficam a saber.)
        self.conhecimento = {}

    def atualizar_conhecimento(self, ambiente, drones, intrusos):
        # 1) Deteção: um intruso ativo é detetado se algum drone o vê dentro do seu alcance.
        ativos = {i.id: i for i in intrusos if i.estado == "ativo"}
        detetados = {}
        for drone in drones:
            visiveis = saltos_ate(ambiente, drone.posicao, drone.alcance_deteccao)
            for id_intruso, intruso in ativos.items():
                if intruso.posicao in visiveis:
                    detetados[id_intruso] = intruso.posicao

        # 2) Esquecer intrusos que já não estão ativos (capturados ou fugidos)
        for id_intruso in list(self.conhecimento):
            if id_intruso not in ativos:
                del self.conhecimento[id_intruso]

        # 3) Guardar as posições vistas agora
        self.conhecimento.update(detetados)

        # 4) Se um drone chegou à última posição conhecida e o intruso não lá está,
        #    a pista perdeu-se: esquecer
        for id_intruso, posicao in list(self.conhecimento.items()):
            if id_intruso not in detetados and any(d.posicao == posicao for d in drones):
                del self.conhecimento[id_intruso]

        return detetados

    def decidir(self, ambiente, drone):
        # Escolhe o alvo conhecido com MENOR CUSTO de deslocação (A*) e devolve o plano.
        # Devolve None se não há alvos conhecidos ou nenhum é alcançável.
        melhor = None
        for id_intruso in sorted(self.conhecimento):       # sorted -> desempate por id
            destino = self.conhecimento[id_intruso]
            r = a_estrela(ambiente, drone.posicao, destino, drone.velocidade)
            if not r["sucesso"]:
                continue
            if melhor is None or r["custo"] < melhor["custo"]:
                melhor = {"alvo": id_intruso, "destino": destino,
                          "caminho": r["caminho"], "custo": r["custo"]}
        return melhor

    def decidir_todos(self, ambiente, drones):
        # Cada drone decide sozinho (sem olhar para o que os outros fazem)
        return {d.id: self.decidir(ambiente, d) for d in drones}