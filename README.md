# Federação de Dados vs. Materialização em ODS — Experimento em Data Mesh

Projeto experimental desenvolvido para um Trabalho de Conclusão de Curso (TCC) em Sistemas de Informação. O estudo compara a **federação de dados com `postgres_fdw`** e a **materialização em um *Operational Data Store* (ODS)** em uma arquitetura organizada por domínios, inspirada nos princípios de *Data Mesh*.

O objetivo é observar como as estratégias se comportam em relação a **tempo de resposta**, **armazenamento** e **custo de atualização/defasagem dos dados**. O projeto é uma prova de conceito acadêmica, não uma implementação completa de Data Mesh ou um ambiente de produção.

## Visão geral da arquitetura

São utilizadas sete instâncias independentes de PostgreSQL em contêineres Docker, na mesma máquina e rede Docker:

| Serviço Docker | Banco de dados | Porta no computador | Papel |
|---|---|---:|---|
| `clientes` | `db_clientes` | 5433 | Domínio Clientes |
| `filiais` | `db_filiais` | 5434 | Domínio Filiais |
| `produtos` | `db_produtos` | 5435 | Domínio Produtos |
| `vendas` | `db_vendas` | 5436 | Domínio Vendas |
| `logistica` | `db_logistica` | 5437 | Domínio Logística |
| `federador` | `db_federador` | 5438 | Integração virtual com `postgres_fdw` |
| `ods` | `db_ods` | 5439 | Tabela materializada `vendas_integradas` |

As fontes permanecem nos cinco domínios nas duas estratégias. Na federação, as consultas acessam *foreign tables* importadas das interfaces `produto_dados`. No ODS, a carga inicial e as cargas incrementais mantêm uma cópia integrada para consulta.

## Tecnologias e requisitos

- Docker e Docker Compose;
- PostgreSQL 16 (`postgres:16` no arquivo Compose; a versão menor pode mudar conforme a imagem disponível);
- Python 3.10 ou superior, com `psycopg` e `openpyxl`;
- Terminal com Docker acessível; os exemplos abaixo utilizam **PowerShell no Windows**.

Na raiz do projeto, instale as bibliotecas Python:

```powershell
py -m pip install -r requirements.txt
```

> **Segurança:** o projeto original utiliza o usuário `tcc` e a senha de **teste** `tcc123` nos contêineres, scripts Python e mapeamentos SQL. Essas credenciais são demonstrativas e não devem ser reutilizadas em serviços reais. Nesta versão de publicação, as portas Docker estão vinculadas a `127.0.0.1` para restringir o acesso à máquina local. Não execute o projeto como serviço público nem exponha as portas na internet.

## Estrutura do repositório

```text
TCC_DataMesh/
├── docker-compose.yml             # Sete instâncias PostgreSQL
├── requirements.txt               # Dependências Python
├── sql/
│   ├── clientes/                  # Estrutura, interface e atualização
│   ├── filiais/
│   ├── produtos/
│   ├── vendas/
│   ├── logistica/
│   ├── federador/                 # postgres_fdw e foreign tables
│   ├── ods/                       # Controle de cargas e vendas_integradas
│   └── consultas_experimentais.sql # C1-C6 para as duas estratégias
├── scripts/
│   ├── geracao_dados/             # Carga das massas e reset
│   ├── carga_ods/                 # Carga inicial, incremental e QP3
│   └── benchmark/                 # Medições e validação das consultas
├── resultados/                   # Planilha consolidada e CSVs oficiais
└── dados/                        # Capturas e planilhas por massa (evidências)
```

O material de evidências também está disponível no [Google Drive](https://drive.google.com/drive/folders/1VkKgtLJxnPo4ie5X5B5j5OSpGKZvneEo?usp=sharing).

## 1. Iniciar o ambiente

Abra o PowerShell **na pasta raiz** `TCC_DataMesh` e execute:

```powershell
docker compose up -d
docker compose ps
```

Antes de criar as estruturas SQL, confirme que os bancos já estão aceitando conexões, por exemplo:

```powershell
docker exec tcc_clientes pg_isready -U tcc -d db_clientes
```

## 2. Criar as estruturas SQL

Os arquivos SQL foram mantidos com os nomes originais, mas **não devem ser executados simplesmente em ordem alfabética ou numérica**: as colunas `data_atualizacao` precisam existir **antes** da criação das *views* que as consultam.

O bloco abaixo executa todos os arquivos necessários na ordem correta, a partir da raiz do projeto. Execute-o **uma única vez após a criação de bancos vazios**:

```powershell
function Invoke-TccSql($container, $banco, $arquivo) {
    Get-Content -Raw -Encoding UTF8 $arquivo | docker exec -i $container psql -v ON_ERROR_STOP=1 -U tcc -d $banco
    if ($LASTEXITCODE -ne 0) { throw "Falha ao executar $arquivo" }
}

$dominios = @(
    @{ c='tcc_clientes';  db='db_clientes';  dir='clientes';  files=@('01_create_cliente.sql','03_add_data_atualizacao.sql','04_create_trigger_data_atualizacao.sql','02_create_interface_cliente.sql') },
    @{ c='tcc_filiais';  db='db_filiais';  dir='filiais';  files=@('01_create_filial.sql','03_add_data_atualizacao.sql','04_create_trigger_data_atualizacao.sql','02_create_interface_filial.sql') },
    @{ c='tcc_produtos'; db='db_produtos'; dir='produtos'; files=@('01_create_produto.sql','03_add_data_atualizacao.sql','04_create_trigger_data_atualizacao.sql','02_create_interface_produto.sql') },
    @{ c='tcc_vendas';   db='db_vendas';   dir='vendas';   files=@('01_create_pedido.sql','02_create_item_pedido.sql','04_add_data_atualizacao.sql','05_create_trigger_data_atualizacao.sql','03_create_interfaces_vendas.sql') },
    @{ c='tcc_logistica';db='db_logistica';dir='logistica';files=@('01_create_entrega.sql','03_add_data_atualizacao.sql','04_create_trigger_data_atualizacao.sql','02_create_interface_entrega.sql') }
)
foreach ($item in $dominios) {
    foreach ($nome in $item.files) {
        Invoke-TccSql $item.c $item.db "sql/$($item.dir)/$nome"
    }
}
foreach ($nome in @('01_create_postgres_fdw.sql','02_create_foreign_servers.sql','03_create_user_mappings.sql','04_import_foreign_tables.sql')) {
    Invoke-TccSql 'tcc_federador' 'db_federador' "sql/federador/$nome"
}
foreach ($nome in @('01_create_controle_carga_ods.sql','02_create_vendas_integradas.sql')) {
    Invoke-TccSql 'tcc_ods' 'db_ods' "sql/ods/$nome"
}
```

O SQL de consultas experimentais reúne comandos para **dois bancos diferentes** e serve como documentação: não execute todo o arquivo `sql/consultas_experimentais.sql` em uma única conexão. O script `benchmark.py` já executa as versões adequadas em cada banco.

## 3. Carregar uma massa e materializar o ODS

As massas são definidas em `scripts/geracao_dados/gerar_massa.py` e carregadas em seus domínios por `carregar_massa.py`. Não é necessário executar `gerar_massa.py` separadamente para criar arquivos de dados: o carregador importa as rotinas de geração.

| Massa | Clientes | Filiais | Produtos | Pedidos |
|---|---:|---:|---:|---:|
| M1 | 5.000 | 100 | 4.000 | 10.000 |
| M2 | 10.000 | 100 | 8.000 | 20.000 |
| M3 | 15.000 | 100 | 12.000 | 30.000 |
| M4 | 20.000 | 100 | 16.000 | 40.000 |
| M5 | 25.000 | 100 | 20.000 | 50.000 |

Exemplo com a massa M1:

```powershell
py scripts/geracao_dados/carregar_massa.py M1
py scripts/carga_ods/carga_inicial.py
py scripts/benchmark/validar_consultas.py
```

O script de validação compara os resultados de C1–C6 nas duas estratégias. **A carga inicial do ODS deve ser executada depois da carga dos domínios.** Não a repita sem limpar previamente os dados materializados.

## 4. Executar o benchmark

Após carregar e validar a massa:

```powershell
py scripts/benchmark/benchmark.py M1
```

O benchmark possui **seis consultas**, **duas estratégias**, **três aquecimentos** e **dez repetições medidas por combinação**. Ao final, os tempos são salvos em `resultados/resultados_benchmark.xlsx`, com abas por massa e resumos, incluindo armazenamento. O cálculo físico de tamanho do banco divide os bytes por `1024²` (MiB), embora a coluna original da planilha seja chamada `Tamanho_MB`.

Para passar de M1 para outra massa, **apague apenas os dados experimentais nos bancos**, mantendo as estruturas SQL:

```powershell
py scripts/geracao_dados/reset_ambiente.py CONFIRMAR
py scripts/geracao_dados/carregar_massa.py M2
py scripts/carga_ods/carga_inicial.py
py scripts/benchmark/validar_consultas.py
py scripts/benchmark/benchmark.py M2
```

Repita o processo para M3, M4 e M5, substituindo o identificador. **O reset é destrutivo:** não o execute se quiser preservar os dados atualmente carregados. Além disso, faça backup do Excel oficial antes de repetir um benchmark, pois o script utiliza esse arquivo como destino e reconhece medições já registradas.

## 5. Atualização incremental e experimento complementar (QP3)

Após a **carga inicial do ODS** (a avaliação complementar foi feita sobre M5), uma sincronização incremental isolada pode ser executada com:

```powershell
py scripts/carga_ods/carga_incremental.py
```

Para monitoramento periódico, use apenas **uma** das opções:

```powershell
py scripts/carga_ods/monitoramento_ods.py --uma-vez
# ou, para sincronizar repetidamente a cada 120 segundos:
py scripts/carga_ods/monitoramento_ods.py --intervalo 120
```

O monitoramento grava `resultados/monitoramento_ods.csv` e pode ser interrompido com **Ctrl+C**.

O experimento complementar altera temporariamente nomes de produtos na origem, executa a sincronização e verifica se as mudanças já aparecem no ODS. Para executá-lo, **interrompa o monitoramento periódico** e utilize:

```powershell
py scripts/carga_ods/experimento_defasagem.py --teste
py scripts/carga_ods/experimento_defasagem.py --executar
```

- `--teste`: uma execução curta de validação, separada dos resultados oficiais;
- `--executar`: cinco repetições para cada lote de **1, 10, 100 e 500** alterações, com intervalo de **120 segundos**;
- `--restaurar`: tenta recuperar os nomes de produtos caso uma execução anterior seja interrompida.

**Importante:** o arquivo oficial `resultados/qp3_experimento.csv` já acompanha o repositório. O script **não o sobrescreve**: para refazer o experimento, primeiro preserve uma cópia do CSV e renomeie o arquivo existente. O experimento restaura os nomes originais após a execução normal. O intervalo medido até a verificação **não corresponde necessariamente ao instante exato do commit no ODS**.

## 6. Resultados e materiais de apoio

- `resultados/resultados_benchmark.xlsx`: arquivo consolidado com as **600 medições válidas** de desempenho, resumo estatístico e armazenamento;
- `resultados/qp3_experimento.csv`: **20 execuções oficiais** de atualização incremental e defasagem;
- `dados/Massa Experimental 1` até `dados/Massa Experimental 5`: capturas de validação, planilhas por massa e registros de armazenamento;
- `dados/Atualização Incremental e Defasagem`: evidências complementares da QP3;
- `sql/consultas_experimentais.sql`: documentação SQL de C1–C6 nas duas estratégias.

As medições foram obtidas em **um único computador**, com instâncias PostgreSQL em contêineres na mesma rede virtual. Assim, o experimento não representa custos típicos de rede entre organizações ou centros de dados distintos. Os resultados de QP3 utilizam somente M5 e momentos controlados de alteração; a defasagem não deve ser extrapolada automaticamente para sistemas em produção.

## Observações de reprodutibilidade

1. A execução dos scripts de criação do esquema pressupõe **bancos vazios**. Para recriar os contêineres e **apagar todos os volumes de banco**, o comando é `docker compose down -v` — utilize-o somente se aceitar perder esses dados.
2. Para comparações de desempenho, mantenha constantes as condições de hardware, Docker, dados, aquecimento e configuração do PostgreSQL; resultados podem variar em outro computador.
3. O repositório contém credenciais **demonstrativas** fixas. Se forem alteradas, ajuste de maneira consistente o Compose, os scripts Python e `sql/federador/03_create_user_mappings.sql` antes de iniciar um novo ambiente.
4. A imagem `postgres:16` não fixa uma atualização menor específica. Para reprodução estrita, registre ou fixe a versão exata utilizada e documente as configurações do ambiente.
5. O material está organizado para fins acadêmicos e de transparência metodológica; não configura software pronto para produção.
