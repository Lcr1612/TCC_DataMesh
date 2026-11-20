CREATE SCHEMA IF NOT EXISTS produto_dados;

CREATE OR REPLACE VIEW produto_dados.vw_entregas AS
SELECT
    id_entrega,
    codigo_entrega,
    id_pedido,
    data_envio,
    data_prevista,
    data_entrega,
    status,
    data_atualizacao
FROM public.entrega;