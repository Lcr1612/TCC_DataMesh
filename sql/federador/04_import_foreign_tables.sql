CREATE SCHEMA IF NOT EXISTS fdw_clientes;
CREATE SCHEMA IF NOT EXISTS fdw_filiais;
CREATE SCHEMA IF NOT EXISTS fdw_produtos;
CREATE SCHEMA IF NOT EXISTS fdw_vendas;
CREATE SCHEMA IF NOT EXISTS fdw_logistica;

IMPORT FOREIGN SCHEMA produto_dados
FROM SERVER srv_clientes
INTO fdw_clientes;

IMPORT FOREIGN SCHEMA produto_dados
FROM SERVER srv_filiais
INTO fdw_filiais;

IMPORT FOREIGN SCHEMA produto_dados
FROM SERVER srv_produtos
INTO fdw_produtos;

IMPORT FOREIGN SCHEMA produto_dados
FROM SERVER srv_vendas
INTO fdw_vendas;

IMPORT FOREIGN SCHEMA produto_dados
FROM SERVER srv_logistica
INTO fdw_logistica;