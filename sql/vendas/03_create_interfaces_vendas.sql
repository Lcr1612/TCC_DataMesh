CREATE SCHEMA IF NOT EXISTS produto_dados;

CREATE OR REPLACE VIEW produto_dados.vw_pedidos AS
SELECT
    id_pedido,
    codigo_pedido,
    data_pedido,
    status,
    valor_total,
    id_cliente,
    id_filial,
    data_atualizacao
FROM public.pedido;

CREATE OR REPLACE VIEW produto_dados.vw_itens_pedido AS
SELECT
    id_pedido,
    id_produto,
    quantidade,
    valor_unitario,
    data_atualizacao
FROM public.item_pedido;