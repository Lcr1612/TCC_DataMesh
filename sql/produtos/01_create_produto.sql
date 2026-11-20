CREATE TABLE produto (
    id_produto INTEGER GENERATED ALWAYS AS IDENTITY,
    codigo_produto VARCHAR(20) NOT NULL,
    nome VARCHAR(100) NOT NULL,
    descricao VARCHAR(200),
    qtd_estoque INTEGER NOT NULL,
    categoria VARCHAR(100) NOT NULL,

    CONSTRAINT pk_produto PRIMARY KEY (id_produto),
    CONSTRAINT uk_produto_codigo UNIQUE (codigo_produto)
);