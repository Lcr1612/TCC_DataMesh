CREATE TABLE pedido (
    id_pedido INTEGER GENERATED ALWAYS AS IDENTITY,
    codigo_pedido VARCHAR(20) NOT NULL,
    data_pedido DATE NOT NULL,
    status VARCHAR(30) NOT NULL,
    valor_total NUMERIC(12,2) NOT NULL,
    id_cliente INTEGER NOT NULL,
    id_filial INTEGER NOT NULL,

    CONSTRAINT pk_pedido PRIMARY KEY (id_pedido),
    CONSTRAINT uk_pedido_codigo UNIQUE (codigo_pedido)
);