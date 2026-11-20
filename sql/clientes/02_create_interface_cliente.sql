CREATE SCHEMA IF NOT EXISTS produto_dados;

CREATE OR REPLACE VIEW produto_dados.vw_clientes AS
SELECT
    id_cliente,
    cpf,
    nome,
    data_atualizacao
FROM public.cliente;