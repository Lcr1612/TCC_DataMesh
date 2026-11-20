CREATE SCHEMA IF NOT EXISTS produto_dados;

CREATE OR REPLACE VIEW produto_dados.vw_produtos AS
SELECT
    id_produto,
    codigo_produto,
    nome,
    categoria,
    data_atualizacao
FROM public.produto;