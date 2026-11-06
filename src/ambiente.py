# AMBIENTE DINÂMICO (por implementar)
# Representar grafo com nós/arestas/custos, portas e barreiras mutáveis, saídas,
# bens e estações de recarga; identificar ligações utilizáveis em cada instante.
# Aplicar eventos de abertura/fecho e verificar a validade dos movimentos e da
# condição de existir uma rota de evacuação válida conforme o enunciado.

class Ambiente:
    def __init__(self):
        self.grafo = {}
        self.portas = {}
        self.barreiras = {}
        self.bens = {}
        self.saidas = set()
        self.estacoes = {}

    # Adicionar uma localização ao edifício
    def adicionar_local(self, local):
        if local not in self.grafo:
            self.grafo[local] = {}

    # Adicionar uma ligação nos dois sentidos
    def adicionar_ligacao(self, origem, destino, comprimento=1):
        if comprimento <= 0:
            raise ValueError("O comprimento deve ser positivo")

        self.adicionar_local(origem)
        self.adicionar_local(destino)

        self.grafo[origem][destino] = comprimento
        self.grafo[destino][origem] = comprimento

    # Associar uma porta a uma ligação existente
    def adicionar_porta(self, origem, destino, aberta=True):
        if destino not in self.grafo.get(origem, {}):
            raise ValueError("A ligação não existe")

        chave = frozenset((origem, destino))
        self.portas[chave] = aberta

    # Abrir ou fechar uma porta
    def alterar_porta(self, origem, destino, aberta):
        chave = frozenset((origem, destino))

        if chave not in self.portas:
            raise ValueError("A porta não existe")

        self.portas[chave] = aberta

    # Associar uma barreira a uma ligação
    def adicionar_barreira(self, origem, destino, ativa=False):
        if destino not in self.grafo.get(origem, {}):
            raise ValueError("A ligação não existe")

        chave = frozenset((origem, destino))
        self.barreiras[chave] = ativa

    # Ativar ou desativar uma barreira
    def alterar_barreira(self, origem, destino, ativa):
        chave = frozenset((origem, destino))

        if chave not in self.barreiras:
            raise ValueError("A barreira não existe")

        self.barreiras[chave] = ativa

    # Adicionar um bem ao edifício
    def adicionar_bem(self, identificador, local, valor):
        if local not in self.grafo:
            raise ValueError("A localização não existe")

        if valor < 0:
            raise ValueError("O valor não pode ser negativo")

        if identificador in self.bens:
            raise ValueError("O bem já existe")

        self.bens[identificador] = {
            "local": local,
            "valor": valor,
            "disponivel": True
        }

    # Adicionar uma saída
    def adicionar_saida(self, local):
        if local not in self.grafo:
            raise ValueError("A localização não existe")

        self.saidas.add(local)

    # Adicionar uma estação de recarga
    def adicionar_estacao(self, identificador, local):
        if local not in self.grafo:
            raise ValueError("A localização não existe")

        if identificador in self.estacoes:
            raise ValueError("A estação já existe")

        self.estacoes[identificador] = {
            "local": local,
            "disponivel": True,
            "drone_a_carregar": None
        }

    # Consultar as ligações atualmente acessíveis
    def vizinhos(self, local):
        if local not in self.grafo:
            raise ValueError("A localização não existe")

        resultado = {}

        for destino, comprimento in self.grafo[local].items():
            chave = frozenset((local, destino))

            porta_aberta = self.portas.get(chave, True)
            barreira_ativa = self.barreiras.get(chave, False)

            if porta_aberta and not barreira_ativa:
                resultado[destino] = comprimento

        return resultado


    # Recolher um bem disponível
    def recolher_bem(self, identificador, local):
        if identificador not in self.bens:
            raise ValueError("O bem não existe")

        bem = self.bens[identificador]

        if not bem["disponivel"]:
            return False

        if bem["local"] != local:
            return False

        bem["disponivel"] = False
        return True




    ###ocupar desocupar estação de recarga
    def ocupar_estacao(self, identificador, drone_id):
        if identificador not in self.estacoes:
            raise ValueError("A estação não existe")

        estacao = self.estacoes[identificador]

        if not estacao["disponivel"]:
            return False

        if estacao["drone_a_carregar"] is not None:
            return False

        estacao["drone_a_carregar"] = drone_id
        return True

    # Libertar uma estação de recarga
    def libertar_estacao(self, identificador, drone_id):
        if identificador not in self.estacoes:
            raise ValueError("A estação não existe")

        estacao = self.estacoes[identificador]

        if estacao["drone_a_carregar"] != drone_id:
            return False

        estacao["drone_a_carregar"] = None
        return True


    # Verificar se existe uma rota até alguma saída
    def existe_rota_saida(self, origem):
        if origem not in self.grafo:
            return False

        visitados = set()
        fila = [origem]

        while fila:
            atual = fila.pop(0)

            if atual in self.saidas:
                return True

            if atual in visitados:
                continue

            visitados.add(atual)

            for vizinho in self.vizinhos(atual):
                if vizinho not in visitados:
                    fila.append(vizinho)

        return False





    @classmethod
    def carregar_json(cls, caminho):
        import json

        with open(caminho, "r", encoding="utf-8") as ficheiro:
            dados = json.load(ficheiro)

        ambiente = cls()

        # Localizações
        for local in dados["mapa"]["nos"]:
            ambiente.adicionar_local(local)

        # Ligações
        for aresta in dados["mapa"]["arestas"]:
            ambiente.adicionar_ligacao(
                aresta["origem"],
                aresta["destino"],
                aresta["comprimento"]
            )

        # Portas
        for porta in dados["portas"]:
            ambiente.adicionar_porta(
                porta["origem"],
                porta["destino"],
                porta["aberta"]
            )

        # Barreiras
        for barreira in dados["barreiras"]:
            ambiente.adicionar_barreira(
                barreira["origem"],
                barreira["destino"],
                barreira["ativa"]
            )

        # Bens
        for bem in dados["bens"]:
            ambiente.adicionar_bem(
                bem["id"],
                bem["local"],
                bem["valor"]
            )

        # Saídas
        for saida in dados["saidas"]:
            ambiente.adicionar_saida(saida)

        # Estações de recarga
        for estacao in dados["recargas"]:
            ambiente.adicionar_estacao(
                estacao["id"],
                estacao["local"]
            )
            ambiente.estacoes[estacao["id"]]["disponivel"] = (
                estacao.get("disponivel", True)
            )

        return ambiente
