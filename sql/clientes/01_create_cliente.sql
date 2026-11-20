CREATE TABLE cliente (
    id_cliente INTEGER GENERATED ALWAYS AS IDENTITY,
    cpf VARCHAR(11) NOT NULL,
    nome VARCHAR(100) NOT NULL,
    endereco VARCHAR(200) NOT NULL,
    telefone VARCHAR(20),

    CONSTRAINT pk_cliente PRIMARY KEY (id_cliente),
    CONSTRAINT uk_cliente_cpf UNIQUE (cpf)
);