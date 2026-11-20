CREATE TABLE controle_carga_ods (
    id_carga INTEGER GENERATED ALWAYS AS IDENTITY,
    tipo_carga VARCHAR(20) NOT NULL,
    inicio_carga TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fim_carga TIMESTAMPTZ,
    data_corte TIMESTAMPTZ NOT NULL,
    registros_processados INTEGER DEFAULT 0,
    status VARCHAR(20) NOT NULL,

    CONSTRAINT pk_controle_carga_ods
        PRIMARY KEY (id_carga),

    CONSTRAINT ck_tipo_carga
        CHECK (tipo_carga IN ('INICIAL', 'INCREMENTAL')),

    CONSTRAINT ck_status_carga
        CHECK (status IN ('EM_EXECUCAO', 'SUCESSO', 'ERRO'))
);