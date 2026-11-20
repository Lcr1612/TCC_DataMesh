CREATE TABLE entrega (
    id_entrega INTEGER GENERATED ALWAYS AS IDENTITY,
    codigo_entrega VARCHAR(20) NOT NULL,
    id_pedido INTEGER NOT NULL,
    data_envio DATE NOT NULL,
    data_prevista DATE NOT NULL,
    data_entrega DATE,
    status VARCHAR(30) NOT NULL,

    CONSTRAINT pk_entrega PRIMARY KEY (id_entrega),
    CONSTRAINT uk_entrega_codigo UNIQUE (codigo_entrega),
    CONSTRAINT uk_entrega_pedido UNIQUE (id_pedido)
);