-- ============================================================================
-- CONSULTAS EXPERIMENTAIS C1 A C6 - FEDERAÇÃO E ODS
-- ============================================================================
-- Fonte: scripts/benchmark/benchmark.py
-- Objetivo: documentar as 12 instruções SQL utilizadas no experimento do TCC.
-- As consultas abaixo reproduzem a lógica SQL do benchmark.py.
--
-- IMPORTANTE: este arquivo reúne SQL de DOIS bancos de dados distintos.
-- Execute as consultas da FEDERAÇÃO conectado ao banco db_federador.
-- Execute as consultas do ODS conectado ao banco db_ods.
-- Não execute o arquivo inteiro em uma única conexão sem alternar de banco.
-- ============================================================================


-- ============================================================================
-- CENÁRIO 1 - FEDERAÇÃO DE DADOS
-- Banco de execução: db_federador
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Consulta C1 | Seletiva
-- Domínios envolvidos: Clientes e Vendas
-- Objetivo: Pedidos concluídos em junho de 2025, com dados dos clientes.
-- ----------------------------------------------------------------------------
SELECT
    p.id_pedido,
    p.codigo_pedido,
    p.data_pedido,
    p.valor_total,
    c.id_cliente,
    c.cpf,
    c.nome
FROM fdw_vendas.vw_pedidos p
JOIN fdw_clientes.vw_clientes c
    ON c.id_cliente = p.id_cliente
WHERE p.status = 'CONCLUIDO'
  AND p.data_pedido >= DATE '2025-06-01'
  AND p.data_pedido < DATE '2025-07-01';

-- ----------------------------------------------------------------------------
-- Consulta C2 | Agregação
-- Domínios envolvidos: Vendas e Produtos
-- Objetivo: Faturamento por categoria de produto para pedidos concluídos.
-- ----------------------------------------------------------------------------
SELECT
    pr.categoria,
    SUM(
        i.quantidade
        * i.valor_unitario
    ) AS faturamento
FROM fdw_vendas.vw_pedidos p
JOIN fdw_vendas.vw_itens_pedido i
    ON i.id_pedido = p.id_pedido
JOIN fdw_produtos.vw_produtos pr
    ON pr.id_produto = i.id_produto
WHERE p.status = 'CONCLUIDO'
GROUP BY pr.categoria
ORDER BY pr.categoria;

-- ----------------------------------------------------------------------------
-- Consulta C3 | Seletiva
-- Domínios envolvidos: Clientes, Filiais e Vendas
-- Objetivo: Pedidos concluídos em filiais de SP, entre abril e junho de 2025.
-- ----------------------------------------------------------------------------
SELECT
    p.id_pedido,
    p.codigo_pedido,
    p.data_pedido,
    p.valor_total,
    c.id_cliente,
    c.nome,
    f.id_filial,
    f.cidade,
    f.uf
FROM fdw_vendas.vw_pedidos p
JOIN fdw_clientes.vw_clientes c
    ON c.id_cliente = p.id_cliente
JOIN fdw_filiais.vw_filiais f
    ON f.id_filial = p.id_filial
WHERE f.uf = 'SP'
  AND p.status = 'CONCLUIDO'
  AND p.data_pedido >= DATE '2025-04-01'
  AND p.data_pedido < DATE '2025-07-01'
ORDER BY p.id_pedido;

-- ----------------------------------------------------------------------------
-- Consulta C4 | Agregação
-- Domínios envolvidos: Filiais, Produtos e Vendas
-- Objetivo: Faturamento por UF e categoria de produto para pedidos concluídos.
-- ----------------------------------------------------------------------------
SELECT
    f.uf,
    pr.categoria,
    SUM(
        i.quantidade
        * i.valor_unitario
    ) AS faturamento
FROM fdw_vendas.vw_pedidos p
JOIN fdw_filiais.vw_filiais f
    ON f.id_filial = p.id_filial
JOIN fdw_vendas.vw_itens_pedido i
    ON i.id_pedido = p.id_pedido
JOIN fdw_produtos.vw_produtos pr
    ON pr.id_produto = i.id_produto
WHERE p.status = 'CONCLUIDO'
GROUP BY
    f.uf,
    pr.categoria
ORDER BY
    f.uf,
    pr.categoria;

-- ----------------------------------------------------------------------------
-- Consulta C5 | Seletiva
-- Domínios envolvidos: Clientes, Filiais, Produtos, Vendas e Logística
-- Objetivo: Itens de pedidos da categoria Informática, em SP, 
--           com entrega realizada e período de julho a setembro de 2025.
-- ----------------------------------------------------------------------------
SELECT
    p.id_pedido,
    p.codigo_pedido,
    p.data_pedido,
    c.nome AS nome_cliente,
    f.cidade,
    f.uf,
    pr.nome AS nome_produto,
    pr.categoria,
    i.quantidade,
    i.valor_unitario,
    e.data_prevista,
    e.data_entrega,
    e.status AS status_entrega
FROM fdw_vendas.vw_pedidos p
JOIN fdw_clientes.vw_clientes c
    ON c.id_cliente = p.id_cliente
JOIN fdw_filiais.vw_filiais f
    ON f.id_filial = p.id_filial
JOIN fdw_vendas.vw_itens_pedido i
    ON i.id_pedido = p.id_pedido
JOIN fdw_produtos.vw_produtos pr
    ON pr.id_produto = i.id_produto
JOIN fdw_logistica.vw_entregas e
    ON e.id_pedido = p.id_pedido
WHERE pr.categoria = 'Informática'
  AND f.uf = 'SP'
  AND e.status = 'ENTREGUE'
  AND p.data_pedido >= DATE '2025-07-01'
  AND p.data_pedido < DATE '2025-10-01'
ORDER BY
    p.id_pedido,
    pr.id_produto;

-- ----------------------------------------------------------------------------
-- Consulta C6 | Agregação
-- Domínios envolvidos: Clientes, Filiais, Produtos, Vendas e Logística
-- Objetivo: Clientes, pedidos, faturamento e prazo médio de entrega por UF e categoria.
-- ----------------------------------------------------------------------------
SELECT
    f.uf,
    pr.categoria,
    COUNT(
        DISTINCT c.id_cliente
    ) AS clientes,
    COUNT(
        DISTINCT p.id_pedido
    ) AS pedidos,
    SUM(
        i.quantidade
        * i.valor_unitario
    ) AS faturamento,
    AVG(
        e.data_entrega
        - p.data_pedido
    ) AS prazo_medio_entrega
FROM fdw_vendas.vw_pedidos p
JOIN fdw_clientes.vw_clientes c
    ON c.id_cliente = p.id_cliente
JOIN fdw_filiais.vw_filiais f
    ON f.id_filial = p.id_filial
JOIN fdw_vendas.vw_itens_pedido i
    ON i.id_pedido = p.id_pedido
JOIN fdw_produtos.vw_produtos pr
    ON pr.id_produto = i.id_produto
JOIN fdw_logistica.vw_entregas e
    ON e.id_pedido = p.id_pedido
WHERE p.status = 'CONCLUIDO'
  AND e.status = 'ENTREGUE'
GROUP BY
    f.uf,
    pr.categoria
ORDER BY
    f.uf,
    pr.categoria;


-- ============================================================================
-- CENÁRIO 2 - MATERIALIZAÇÃO EM ODS
-- Banco de execução: db_ods
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Consulta C1 | Seletiva
-- Domínios envolvidos: Clientes e Vendas
-- Objetivo: Pedidos concluídos em junho de 2025, com dados dos clientes.
-- ----------------------------------------------------------------------------
SELECT DISTINCT
    id_pedido,
    codigo_pedido,
    data_pedido,
    valor_total,
    id_cliente,
    cpf,
    nome_cliente
FROM public.vendas_integradas
WHERE status_pedido = 'CONCLUIDO'
  AND data_pedido >= DATE '2025-06-01'
  AND data_pedido < DATE '2025-07-01';

-- ----------------------------------------------------------------------------
-- Consulta C2 | Agregação
-- Domínios envolvidos: Vendas e Produtos
-- Objetivo: Faturamento por categoria de produto para pedidos concluídos.
-- ----------------------------------------------------------------------------
SELECT
    categoria,
    SUM(
        quantidade
        * valor_unitario
    ) AS faturamento
FROM public.vendas_integradas
WHERE status_pedido = 'CONCLUIDO'
GROUP BY categoria
ORDER BY categoria;

-- ----------------------------------------------------------------------------
-- Consulta C3 | Seletiva
-- Domínios envolvidos: Clientes, Filiais e Vendas
-- Objetivo: Pedidos concluídos em filiais de SP, entre abril e junho de 2025.
-- ----------------------------------------------------------------------------
SELECT DISTINCT
    id_pedido,
    codigo_pedido,
    data_pedido,
    valor_total,
    id_cliente,
    nome_cliente,
    id_filial,
    cidade,
    uf
FROM public.vendas_integradas
WHERE uf = 'SP'
  AND status_pedido = 'CONCLUIDO'
  AND data_pedido >= DATE '2025-04-01'
  AND data_pedido < DATE '2025-07-01'
ORDER BY id_pedido;

-- ----------------------------------------------------------------------------
-- Consulta C4 | Agregação
-- Domínios envolvidos: Filiais, Produtos e Vendas
-- Objetivo: Faturamento por UF e categoria de produto para pedidos concluídos.
-- ----------------------------------------------------------------------------
SELECT
    uf,
    categoria,
    SUM(
        quantidade
        * valor_unitario
    ) AS faturamento
FROM public.vendas_integradas
WHERE status_pedido = 'CONCLUIDO'
GROUP BY
    uf,
    categoria
ORDER BY
    uf,
    categoria;

-- ----------------------------------------------------------------------------
-- Consulta C5 | Seletiva
-- Domínios envolvidos: Clientes, Filiais, Produtos, Vendas e Logística
-- Objetivo: Itens de pedidos da categoria Informática, em SP, 
--           com entrega realizada e período de julho a setembro de 2025.
-- ----------------------------------------------------------------------------
SELECT
    id_pedido,
    codigo_pedido,
    data_pedido,
    nome_cliente,
    cidade,
    uf,
    nome_produto,
    categoria,
    quantidade,
    valor_unitario,
    data_prevista,
    data_entrega,
    status_entrega
FROM public.vendas_integradas
WHERE categoria = 'Informática'
  AND uf = 'SP'
  AND status_entrega = 'ENTREGUE'
  AND data_pedido >= DATE '2025-07-01'
  AND data_pedido < DATE '2025-10-01'
ORDER BY
    id_pedido,
    id_produto;

-- ----------------------------------------------------------------------------
-- Consulta C6 | Agregação
-- Domínios envolvidos: Clientes, Filiais, Produtos, Vendas e Logística
-- Objetivo: Clientes, pedidos, faturamento e prazo médio de entrega por UF e categoria.
-- ----------------------------------------------------------------------------
SELECT
    uf,
    categoria,
    COUNT(
        DISTINCT id_cliente
    ) AS clientes,
    COUNT(
        DISTINCT id_pedido
    ) AS pedidos,
    SUM(
        quantidade
        * valor_unitario
    ) AS faturamento,
    AVG(
        data_entrega
        - data_pedido
    ) AS prazo_medio_entrega
FROM public.vendas_integradas
WHERE status_pedido = 'CONCLUIDO'
  AND status_entrega = 'ENTREGUE'
GROUP BY
    uf,
    categoria
ORDER BY
    uf,
    categoria;