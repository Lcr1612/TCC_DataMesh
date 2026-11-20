CREATE SERVER srv_clientes
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (
    host 'clientes',
    port '5432',
    dbname 'db_clientes'
);

CREATE SERVER srv_filiais
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (
    host 'filiais',
    port '5432',
    dbname 'db_filiais'
);

CREATE SERVER srv_produtos
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (
    host 'produtos',
    port '5432',
    dbname 'db_produtos'
);

CREATE SERVER srv_vendas
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (
    host 'vendas',
    port '5432',
    dbname 'db_vendas'
);

CREATE SERVER srv_logistica
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (
    host 'logistica',
    port '5432',
    dbname 'db_logistica'
);