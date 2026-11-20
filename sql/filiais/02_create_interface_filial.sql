CREATE SCHEMA IF NOT EXISTS produto_dados;

CREATE OR REPLACE VIEW produto_dados.vw_filiais AS
SELECT
    id_filial,
    cnpj_filial,
    uf,
    cidade,
    data_atualizacao
FROM public.filial;