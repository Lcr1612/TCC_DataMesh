CREATE TABLE item_pedido (
    id_pedido INTEGER NOT NULL,
    id_produto INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    valor_unitario NUMERIC(12,2) NOT NULL,

    CONSTRAINT pk_item_pedido
        PRIMARY KEY (id_pedido, id_produto),

    CONSTRAINT fk_item_pedido_pedido
        FOREIGN KEY (id_pedido)
        REFERENCES pedido(id_pedido)
);