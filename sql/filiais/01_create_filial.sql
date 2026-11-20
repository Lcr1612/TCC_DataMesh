CREATE TABLE filial (
    id_filial INTEGER GENERATED ALWAYS AS IDENTITY,
    cnpj_filial VARCHAR(14) NOT NULL,
    uf VARCHAR(2) NOT NULL,
    cidade VARCHAR(100) NOT NULL,
    endereco VARCHAR(200) NOT NULL,
    telefone VARCHAR(20),

    CONSTRAINT pk_filial PRIMARY KEY (id_filial),
    CONSTRAINT uk_filial_cnpj UNIQUE (cnpj_filial)
);