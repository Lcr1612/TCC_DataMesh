CREATE TABLE vendas_integradas (
    id_pedido INTEGER NOT NULL,
    codigo_pedido VARCHAR(20) NOT NULL,
    data_pedido DATE NOT NULL,
    status_pedido VARCHAR(30) NOT NULL,
    valor_total NUMERIC(12,2) NOT NULL,

    id_cliente INTEGER NOT NULL,
    cpf VARCHAR(11) NOT NULL,
    nome_cliente VARCHAR(100) NOT NULL,

    id_filial INTEGER NOT NULL,
    cnpj_filial VARCHAR(14) NOT NULL,
    uf VARCHAR(2) NOT NULL,
    cidade VARCHAR(100) NOT NULL,

    id_produto INTEGER NOT NULL,
    codigo_produto VARCHAR(20) NOT NULL,
    nome_produto VARCHAR(100) NOT NULL,
    categoria VARCHAR(100) NOT NULL,
    quantidade INTEGER NOT NULL,
    valor_unitario NUMERIC(12,2) NOT NULL,

    id_entrega INTEGER NOT NULL,
    data_envio DATE NOT NULL,
    data_prevista DATE NOT NULL,
    data_entrega DATE,
    status_entrega VARCHAR(30) NOT NULL,

    data_atualizacao_origem TIMESTAMPTZ NOT NULL,
    data_carga_ods TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_vendas_integradas
        PRIMARY KEY (id_pedido, id_produto)
);