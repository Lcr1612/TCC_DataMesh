import random
import sys
from datetime import date, timedelta
from decimal import Decimal

TAMANHO_LOTE = 5_000
DATA_INICIAL = date(2025, 1, 1)
DATA_FINAL = date(2025, 12, 31)

# Semente fixa para garantir reprodutibilidade
SEMENTE = 2025

random.seed(SEMENTE)

# Configuração das massas experimentais

MASSAS = {
    "M1": {
        "clientes": 5_000,
        "filiais": 100,
        "produtos": 4_000,
        "pedidos": 10_000
    },
    "M2": {
        "clientes": 10_000,
        "filiais": 100,
        "produtos": 8_000,
        "pedidos": 20_000
    },
    "M3": {
        "clientes": 15_000,
        "filiais": 100,
        "produtos": 12_000,
        "pedidos": 30_000
    },
    "M4": {
        "clientes": 20_000,
        "filiais": 100,
        "produtos": 16_000,
        "pedidos": 40_000
    },
    "M5": {
        "clientes": 25_000,
        "filiais": 100,
        "produtos": 20_000,
        "pedidos": 50_000
    }
}

CATALOGO_PRODUTOS = {
    "Eletrônicos": {
        "Smartphone": (600, 7000),
        "Televisão": (900, 8000),
        "Fone Bluetooth": (80, 1500),
        "Smartwatch": (150, 3500),
        "Câmera": (800, 9000),
        "Videogame": (2200, 6500),
        "Jogo de Videogame": (80, 550),
        "Notebook": (2000, 15000),
        "Computadores": (1500, 12000)
    },

    "Eletrodomésticos": {
        "Geladeira": (1500, 8000),
        "Micro-ondas": (400, 1800),
        "Liquidificador": (80, 600),
        "Air Fryer": (250, 1500),
        "Aspirador": (150, 300)
    },

    "Informática": {
        "Monitor": (500, 4000),
        "Teclado": (50, 1200),
        "Mouse": (30, 700),
        "SSD": (120, 1500),
        "Placa-mãe": (350, 3000),
        "Memória RAM": (100, 1500),
        "Processador": (400, 5000),
        "Fonte": (200, 1500),
        "Gabinete": (150, 1500)
    },

    "Móveis": {
        "Mesa": (200, 3000),
        "Cadeira": (150, 2500),
        "Estante": (180, 2500),
        "Guarda-roupa": (600, 5000)
    },

    "Casa e Utilidades": {
        "Panela": (30, 700),
        "Jogo de Copos": (20, 300),
        "Toalha": (20, 250),
        "Luminária": (40, 800)
    },

    "Esporte e Lazer": {
        "Bicicleta": (600, 6000),
        "Bola": (40, 500),
        "Raquete": (100, 2500),
        "Skate": (120, 800)
    },

    "Vestuário": {
        "Camisa": (30, 300),
        "Calça": (60, 600),
        "Jaqueta": (100, 1200),
        "Tênis": (100, 1500)
    },

    "Beleza e Cuidados": {
        "Perfume": (160, 2000),
        "Secador": (180, 900),
        "Hidratante": (20, 300),
        "Shampoo": (15, 200)
    },

    "Brinquedos": {
        "Boneca": (30, 700),
        "Carrinho": (20, 500),
        "Jogo de Tabuleiro": (40, 500),
        "Quebra-cabeça": (80, 650)
    },

    "Papelaria": {
        "Caderno": (10, 100),
        "Caneta": (3, 50),
        "Mochila": (60, 600),
        "Estojo": (15, 150)
    }
}

##########

NOMES = [
    "Gabriel", "Lucas", "Rafael", "Matheus", "Pedro",
    "Felipe", "Bruno", "Thiago", "Gustavo", "Leonardo",
    "Ana", "Mariana", "Juliana", "Beatriz", "Camila",
    "Larissa", "Isabela", "Amanda", "Carolina", "Leticia"
]

SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues",
    "Ferreira", "Almeida", "Costa", "Gomes", "Martins",
    "Pereira", "Carvalho", "Lima", "Rocha", "Ribeiro",
    "Barbosa", "Moura", "Freitas", "Teixeira", "Azevedo"
]

TIPOS_LOGRADOURO = [
    "Rua",
    "Avenida",
    "Travessa",
    "Alameda"
]

NOMES_LOGRADOURO = [
    "das Acácias",
    "das Palmeiras",
    "do Horizonte",
    "das Flores",
    "dos Ipês",
    "do Sol",
    "da Esperança",
    "das Oliveiras",
    "do Bosque",
    "das Orquídeas",
    "Central",
    "Boa Vista"
]

LOCALIDADES = [
    {
        "cidade": "Niterói",
        "uf": "RJ",
        "ddd": "21",
        "bairros": ["Icaraí", "Santa Rosa", "Centro", "Fonseca"]
    },
    {
        "cidade": "Rio de Janeiro",
        "uf": "RJ",
        "ddd": "21",
        "bairros": ["Tijuca", "Copacabana", "Botafogo", "Méier"]
    },
    {
        "cidade": "São Paulo",
        "uf": "SP",
        "ddd": "11",
        "bairros": ["Pinheiros", "Mooca", "Santana", "Vila Mariana"]
    },
    {
        "cidade": "Belo Horizonte",
        "uf": "MG",
        "ddd": "31",
        "bairros": ["Centro", "Savassi", "Pampulha", "Buritis"]
    },
    {
        "cidade": "Curitiba",
        "uf": "PR",
        "ddd": "41",
        "bairros": ["Centro", "Batel", "Água Verde", "Cabral"]
    },
    {
        "cidade": "Salvador",
        "uf": "BA",
        "ddd": "71",
        "bairros": ["Barra", "Pituba", "Itapuã", "Brotas"]
    },
    {
        "cidade": "Recife",
        "uf": "PE",
        "ddd": "81",
        "bairros": ["Boa Viagem", "Casa Forte", "Madalena", "Centro"]
    },
    {
        "cidade": "Porto Alegre",
        "uf": "RS",
        "ddd": "51",
        "bairros": ["Centro Histórico", "Moinhos de Vento", "Menino Deus", "Petrópolis"]
    }
]


MARCAS = [
    "Lumina", "Vértice", "Nexa", "Atria", "Orion",
    "Viva", "Atlas", "Nova", "Pulse", "Prime",
    "Solaris", "Urban", "Essenza", "Mira", "Horizon"
]

LINHAS = [
    "Essential", "Plus", "Prime", "Pro", "Max",
    "Smart", "Classic", "Flex", "Advance", "Premium"
]


# Distribuição da quantidade de itens por pedido
QUANTIDADE_ITENS = [1, 2, 3, 4, 5, 6]

PESOS_ITENS = [
    0.05,  # 1 item
    0.10,  # 2 itens
    0.15,  # 3 itens
    0.35,  # 4 itens
    0.20,  # 5 itens
    0.15   # 6 itens
]


# Distribuição dos status dos pedidos
STATUS_PEDIDOS = [
    "CONCLUIDO",
    "CANCELADO",
    "REEMBOLSADO"
]

PESOS_STATUS_PEDIDOS = [
    0.85,
    0.10,
    0.05
]

def dividir_em_lotes(iteravel, tamanho=TAMANHO_LOTE):
    lote = []

    for registro in iteravel:
        lote.append(registro)

        if len(lote) >= tamanho:
            yield lote
            lote = []

    if lote:
        yield lote

##Clientes

def gerar_clientes_teste(quantidade=5):
    clientes = []
    cpfs_usados = set()
    telefones_usados = set()

    for _ in range(quantidade):

        # CPF aleatório com 11 dígitos e sem repetição
        while True:
            cpf = f"{random.randint(0, 99_999_999_999):011d}"

            if cpf not in cpfs_usados:
                cpfs_usados.add(cpf)
                break

        # Nome com dois sobrenomes diferentes
        primeiro_nome = random.choice(NOMES)
        sobrenome1, sobrenome2 = random.sample(SOBRENOMES, 2)

        nome_completo = (
            f"{primeiro_nome} {sobrenome1} {sobrenome2}"
        )

        # Localidade
        localidade = random.choice(LOCALIDADES)

        tipo_logradouro = random.choice(TIPOS_LOGRADOURO)
        nome_logradouro = random.choice(NOMES_LOGRADOURO)
        numero = random.randint(1, 3000)
        bairro = random.choice(localidade["bairros"])

        endereco = (
            f"{tipo_logradouro} {nome_logradouro}, {numero} - "
            f"{bairro}, {localidade['cidade']}/{localidade['uf']}"
        )

        # Telefone com DDD coerente com a cidade
        while True:
            telefone = (
                f"{localidade['ddd']}9"
                f"{random.randint(10_000_000, 99_999_999)}"
            )

            if telefone not in telefones_usados:
                telefones_usados.add(telefone)
                break

        clientes.append({
            "nome": nome_completo,
            "cpf": cpf,
            "endereco": endereco,
            "telefone": telefone
        })

    return clientes

def gerar_clientes_em_lotes(
    quantidade_total,
    tamanho_lote=TAMANHO_LOTE
):
    cpfs_usados = set()
    telefones_usados = set()

    lote = []

    for _ in range(quantidade_total):

        # CPF único
        while True:
            cpf = f"{random.randint(0, 99_999_999_999):011d}"

            if cpf not in cpfs_usados:
                cpfs_usados.add(cpf)
                break

        # Nome
        primeiro_nome = random.choice(NOMES)

        sobrenome1, sobrenome2 = random.sample(
            SOBRENOMES,
            2
        )

        nome_completo = (
            f"{primeiro_nome} "
            f"{sobrenome1} "
            f"{sobrenome2}"
        )

        # Localidade
        localidade = random.choice(LOCALIDADES)

        tipo_logradouro = random.choice(
            TIPOS_LOGRADOURO
        )

        nome_logradouro = random.choice(
            NOMES_LOGRADOURO
        )

        numero = random.randint(1, 3000)

        bairro = random.choice(
            localidade["bairros"]
        )

        endereco = (
            f"{tipo_logradouro} "
            f"{nome_logradouro}, "
            f"{numero} - "
            f"{bairro}, "
            f"{localidade['cidade']}/"
            f"{localidade['uf']}"
        )

        # Telefone único
        while True:
            telefone = (
                f"{localidade['ddd']}9"
                f"{random.randint(10_000_000, 99_999_999)}"
            )

            if telefone not in telefones_usados:
                telefones_usados.add(telefone)
                break

        lote.append({
            "nome": nome_completo,
            "cpf": cpf,
            "endereco": endereco,
            "telefone": telefone
        })

        if len(lote) >= tamanho_lote:
            yield lote
            lote = []

    # Último lote, caso não complete 5.000
    if lote:
        yield lote

#### Filiais

def gerar_filiais_teste(quantidade=5):
    filiais = []
    cnpjs_usados = set()
    telefones_usados = set()

    for _ in range(quantidade):

        # CNPJ aleatório com 14 dígitos e sem repetição
        while True:
            cnpj = f"{random.randint(0, 99_999_999_999_999):014d}"

            if cnpj not in cnpjs_usados:
                cnpjs_usados.add(cnpj)
                break

        # Localidade
        localidade = random.choice(LOCALIDADES)

        tipo_logradouro = random.choice(TIPOS_LOGRADOURO)
        nome_logradouro = random.choice(NOMES_LOGRADOURO)
        numero = random.randint(1, 3000)
        bairro = random.choice(localidade["bairros"])

        endereco = (
            f"{tipo_logradouro} {nome_logradouro}, {numero} - "
            f"{bairro}, {localidade['cidade']}/{localidade['uf']}"
        )

        # Telefone fixo com DDD coerente com a cidade
        while True:
            telefone = (
                f"{localidade['ddd']}"
                f"{random.randint(20_000_000, 59_999_999)}"
            )

            if telefone not in telefones_usados:
                telefones_usados.add(telefone)
                break

        filiais.append({
            "cnpj_filial": cnpj,
            "uf": localidade["uf"],
            "cidade": localidade["cidade"],
            "endereco": endereco,
            "telefone": telefone
        })

    return filiais

### Produtos

def gerar_produtos_teste(quantidade=10):
    produtos = []

    codigos_usados = set()
    chaves_produtos_usadas = set()

    categorias = list(CATALOGO_PRODUTOS.keys())

    while len(produtos) < quantidade:

        categoria = random.choice(categorias)

        tipos_produto = list(
            CATALOGO_PRODUTOS[categoria].keys()
        )

        tipo_produto = random.choice(tipos_produto)

        marca = random.choice(MARCAS)
        linha = random.choice(LINHAS)

        letras_modelo = "".join(
            random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2)
        )

        numero_modelo = random.randint(100, 9999)

        modelo = f"{letras_modelo}-{numero_modelo}"

        # Identidade lógica do produto:
        # tipo + marca + linha + modelo.
        chave_produto = (
            tipo_produto,
            marca,
            linha,
            modelo
        )

        # Se a mesma combinação já existir, trata-se do mesmo
        # produto e outra combinação deve ser gerada.
        if chave_produto in chaves_produtos_usadas:
            continue

        chaves_produtos_usadas.add(chave_produto)

        # Código único e independente do ID.
        while True:
            codigo_produto = (
                f"PRD-{random.randint(10000000, 99999999)}"
            )

            if codigo_produto not in codigos_usados:
                codigos_usados.add(codigo_produto)
                break

        nome_produto = (
            f"{tipo_produto} {marca} {linha} {modelo}"
        )

        descricao = (
            f"{tipo_produto} {marca}, linha {linha}, "
            f"modelo {modelo}"
        )

        qtd_estoque = random.randint(0, 500)

        # Preço-base auxiliar do gerador. Não será uma coluna
        # da tabela produto; serve para manter os preços das
        # diferentes vendas do mesmo produto em uma faixa coerente.
        valor_minimo, valor_maximo = (
            CATALOGO_PRODUTOS[categoria][tipo_produto]
        )

        preco_base = Decimal(
            str(
                round(
                    random.uniform(valor_minimo, valor_maximo),
                    2
                )
            )
        )

        produtos.append({
            "codigo_produto": codigo_produto,
            "nome": nome_produto,
            "descricao": descricao,
            "qtd_estoque": qtd_estoque,
            "categoria": categoria,

            # Campos auxiliares usados somente pelo gerador.
            "tipo_produto": tipo_produto,
            "marca": marca,
            "linha": linha,
            "modelo": modelo,
            "preco_base": preco_base
        })

    return produtos

###### Pedido

def criar_pesos_distribuicao(quantidade):
    """
    Cria pesos para uma distribuição não uniforme.
    Uma parcela menor dos registros terá maior chance
    de ser selecionada.
    """
    indices = list(range(quantidade))
    random.shuffle(indices)

    qtd_alta = int(quantidade * 0.20)
    qtd_media = int(quantidade * 0.30)

    pesos = [1.0] * quantidade

    for indice in indices[:qtd_alta]:
        pesos[indice] = 5.0

    for indice in indices[qtd_alta:qtd_alta + qtd_media]:
        pesos[indice] = 2.0

    return pesos


def escolher_sem_repeticao(elementos, pesos, quantidade):
    """
    Realiza seleção ponderada sem permitir que o mesmo
    elemento seja escolhido duas vezes.
    """
    elementos_disponiveis = list(elementos)
    pesos_disponiveis = list(pesos)

    escolhidos = []

    for _ in range(quantidade):
        escolhido = random.choices(
            elementos_disponiveis,
            weights=pesos_disponiveis,
            k=1
        )[0]

        indice = elementos_disponiveis.index(escolhido)

        escolhidos.append(escolhido)

        elementos_disponiveis.pop(indice)
        pesos_disponiveis.pop(indice)

    return escolhidos

## Entrega

def gerar_data_pedido():
    dias_periodo = (DATA_FINAL - DATA_INICIAL).days

    return (
        DATA_INICIAL
        + timedelta(days=random.randint(0, dias_periodo))
    )


def gerar_dados_entrega(data_pedido, status_pedido):
    # Envio entre 0 e 3 dias após o pedido
    data_envio = (
        data_pedido
        + timedelta(days=random.randint(0, 3))
    )

    # Previsão entre 2 e 10 dias após o envio
    data_prevista = (
        data_envio
        + timedelta(days=random.randint(2, 10))
    )

    if status_pedido == "CANCELADO":
        return {
            "data_envio": data_envio,
            "data_prevista": data_prevista,
            "data_entrega": None,
            "status_entrega": "CANCELADA"
        }

    if status_pedido == "REEMBOLSADO":
        data_entrega = (
            data_envio
            + timedelta(days=random.randint(1, 10))
        )

        return {
            "data_envio": data_envio,
            "data_prevista": data_prevista,
            "data_entrega": data_entrega,
            "status_entrega": "DEVOLVIDA"
        }

    # Pedidos concluídos:
    # 20% das entregas chegam após o prazo
    atrasada = random.random() < 0.20

    if atrasada:
        data_entrega = (
            data_prevista
            + timedelta(days=random.randint(1, 7))
        )
    else:
        dias_ate_previsao = (
            data_prevista - data_envio
        ).days

        data_entrega = (
            data_envio
            + timedelta(
                days=random.randint(1, dias_ate_previsao)
            )
        )

    return {
        "data_envio": data_envio,
        "data_prevista": data_prevista,
        "data_entrega": data_entrega,
        "status_entrega": "ENTREGUE"
    }


def gerar_valor_unitario(produto):
    preco_base = produto["preco_base"]

    # O mesmo produto pode ter pequenas variações de preço
    # entre vendas, simulando promoções e reajustes.
    variacao = Decimal(
        str(
            round(
                random.uniform(0.85, 1.15),
                4
            )
        )
    )

    valor_unitario = preco_base * variacao

    return valor_unitario.quantize(
        Decimal("0.01")
    )

def gerar_vendas_teste(
    clientes,
    filiais,
    produtos,
    quantidade_pedidos=20
):
    pedidos = []
    itens_pedido = []
    entregas = []

    codigos_pedido_usados = set()
    codigos_entrega_usados = set()

    # IDs simulados.
    # Depois do reset oficial, as tabelas serão inseridas
    # nessa mesma ordem e os IDs começarão em 1.
    ids_clientes = list(range(1, len(clientes) + 1))
    ids_filiais = list(range(1, len(filiais) + 1))
    ids_produtos = list(range(1, len(produtos) + 1))

    # Aproximadamente 90% dos clientes participam das vendas.
    quantidade_clientes_ativos = max(
        1,
        round(len(clientes) * 0.90)
    )

    clientes_ativos = random.sample(
        ids_clientes,
        quantidade_clientes_ativos
    )

    # Pesos não uniformes para filiais e produtos.
    pesos_filiais = criar_pesos_distribuicao(
        len(filiais)
    )

    pesos_produtos = criar_pesos_distribuicao(
        len(produtos)
    )

    # Garante inicialmente pelo menos um pedido para cada
    # cliente considerado ativo, quando o número de pedidos
    # disponível permite isso.
    clientes_dos_pedidos = []

    for id_cliente in clientes_ativos:
        if len(clientes_dos_pedidos) < quantidade_pedidos:
            clientes_dos_pedidos.append(id_cliente)

    # Os pedidos restantes são distribuídos entre os clientes
    # ativos, permitindo múltiplas compras.
    while len(clientes_dos_pedidos) < quantidade_pedidos:
        clientes_dos_pedidos.append(
            random.choice(clientes_ativos)
        )

    random.shuffle(clientes_dos_pedidos)

    # ---------------------------------------------------------
    # PEDIDOS E ITENS DE PEDIDO
    # ---------------------------------------------------------
    for numero_pedido in range(1, quantidade_pedidos + 1):

        id_cliente = clientes_dos_pedidos[
            numero_pedido - 1
        ]

        id_filial = random.choices(
            ids_filiais,
            weights=pesos_filiais,
            k=1
        )[0]

        # Código de pedido único e independente do ID.
        while True:
            codigo_pedido = (
                f"PED-{random.randint(1000000000, 9999999999)}"
            )

            if codigo_pedido not in codigos_pedido_usados:
                codigos_pedido_usados.add(codigo_pedido)
                break

        data_pedido = gerar_data_pedido()

        status_pedido = random.choices(
            STATUS_PEDIDOS,
            weights=PESOS_STATUS_PEDIDOS,
            k=1
        )[0]

        quantidade_itens = random.choices(
            QUANTIDADE_ITENS,
            weights=PESOS_ITENS,
            k=1
        )[0]

        # Não permite mais itens do que produtos disponíveis.
        quantidade_itens = min(
            quantidade_itens,
            len(produtos)
        )

        produtos_escolhidos = escolher_sem_repeticao(
            ids_produtos,
            pesos_produtos,
            quantidade_itens
        )

        itens_do_pedido = []
        valor_total = Decimal("0.00")

        for id_produto in produtos_escolhidos:

            produto = produtos[id_produto - 1]

            quantidade = random.randint(1, 5)

            valor_unitario = gerar_valor_unitario(
                produto
            )

            subtotal = valor_unitario * quantidade
            valor_total += subtotal

            item = {
                "id_pedido": numero_pedido,
                "id_produto": id_produto,
                "quantidade": quantidade,
                "valor_unitario": valor_unitario
            }

            itens_do_pedido.append(item)

        valor_total = valor_total.quantize(
            Decimal("0.01")
        )

        pedido = {
            "id_pedido": numero_pedido,
            "codigo_pedido": codigo_pedido,
            "data_pedido": data_pedido,
            "status": status_pedido,
            "valor_total": valor_total,
            "id_cliente": id_cliente,
            "id_filial": id_filial
        }

        pedidos.append(pedido)
        itens_pedido.extend(itens_do_pedido)

    # ---------------------------------------------------------
    # ENTREGAS
    # ---------------------------------------------------------
    # A relação continua sendo 1:1, porém os IDs das entregas
    # são independentes dos IDs dos pedidos. Assim, por exemplo,
    # id_entrega 1 pode estar associado ao id_pedido 6.
    ids_pedidos_para_entrega = list(
        range(1, quantidade_pedidos + 1)
    )

    random.shuffle(ids_pedidos_para_entrega)

    for numero_entrega, id_pedido in enumerate(
        ids_pedidos_para_entrega,
        start=1
    ):

        pedido = pedidos[id_pedido - 1]

        dados_entrega = gerar_dados_entrega(
            pedido["data_pedido"],
            pedido["status"]
        )

        # Código de entrega único e independente do ID.
        while True:
            codigo_entrega = (
                f"ENT-{random.randint(1000000000, 9999999999)}"
            )

            if codigo_entrega not in codigos_entrega_usados:
                codigos_entrega_usados.add(codigo_entrega)
                break

        entrega = {
            "id_entrega": numero_entrega,
            "codigo_entrega": codigo_entrega,
            "id_pedido": id_pedido,
            "data_envio": dados_entrega["data_envio"],
            "data_prevista": dados_entrega["data_prevista"],
            "data_entrega": dados_entrega["data_entrega"],
            "status": dados_entrega["status_entrega"]
        }

        entregas.append(entrega)

    return pedidos, itens_pedido, entregas

######################################

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Uso: py gerar_massa.py M1")
        raise SystemExit

    massa_escolhida = sys.argv[1].upper()

    if massa_escolhida not in MASSAS:
        print(
            f"Massa inválida: {massa_escolhida}. "
            f"Escolha entre: {', '.join(MASSAS.keys())}"
        )
        raise SystemExit

    configuracao = MASSAS[massa_escolhida]

    print(f"Massa selecionada: {massa_escolhida}")
    print(f"Clientes: {configuracao['clientes']}")
    print(f"Filiais: {configuracao['filiais']}")
    print(f"Produtos: {configuracao['produtos']}")
    print(f"Pedidos: {configuracao['pedidos']}")
