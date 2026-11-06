# AGENTES E COMPORTAMENTOS (por implementar)
# Definir drones (posição, velocidade, autonomia, custo, recarga) e intrusos
# (posição, velocidade, bens recolhidos, estado da missão).
# Criar pelo menos dois perfis distintos: um mais orientado à recolha de bens
# e outro à evasão/fuga; definir como escolhem ações e reagem ao ambiente.

class Drone:
    def __init__(
        self, id, posicao, velocidade,
        energia_atual, energia_max,
        consumo_movimento, consumo_parado,
        taxa_recarga,
        custo_ativacao, custo_voo,
        custo_parado, custo_recarga
    ):
        self.id = id
        self.posicao = posicao
        self.velocidade = velocidade

        # Bateria
        self.energia_atual = energia_atual
        self.energia_max = energia_max
        self.consumo_movimento = consumo_movimento
        self.consumo_parado = consumo_parado
        self.taxa_recarga = taxa_recarga

        # Custos operacionais
        self.custo_ativacao = custo_ativacao
        self.custo_voo = custo_voo
        self.custo_parado = custo_parado
        self.custo_recarga = custo_recarga

        # Estado da missão
        self.tarefa = None
        self.estado = "disponivel"

        # Estatísticas
        self.passos_movimento = 0
        self.passos_parado = 0
        self.numero_recargas = 0
        self.foi_ativado = False



class Intruso:
    def __init__(
        self, id, posicao, velocidade,
        perfil, tempo_entrada=0
    ):
        self.id = id
        self.posicao = posicao
        self.velocidade = velocidade
        self.perfil = perfil

        self.bens_recolhidos = []
        self.estado = "ativo"
        self.tempo_entrada = tempo_entrada

        # Objetivo atual do intruso
        self.objetivo = None
