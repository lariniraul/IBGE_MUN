# Consulta Municipal • SP

Aplicação Python local com interface no navegador. Consulta receitas e despesas da API pública do TCE-SP, por cidade e intervalo de meses, e indicadores municipais do IBGE. Não exige chave de API. Requer Python 3.10 ou superior e internet.

## Iniciar

Abra um terminal nesta pasta e execute:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

O Streamlit abre o navegador. Se não abrir automaticamente, acesse http://localhost:8501. Para encerrar, pressione Ctrl+C no terminal.

## Usar

1. Escolha Receitas ou Despesas no menu lateral.
2. Escolha a cidade; o padrão é Cosmópolis/SP.
3. Informe início e fim em MM/AAAA; o padrão é janeiro de 2026.
4. Clique em Consultar. As tabelas e resumos aparecem na tela, sem download.
5. Veja o resumo de todos os meses. Use Mês dos detalhes para acessar um mês diretamente.
6. Filtre por órgão e fonte ou movimentação, busque texto e navegue entre páginas. Por padrão, a tabela inclui todos os registros; escolha 25, 50 ou 100 linhas para paginar.

A exportação CSV é opcional e inclui todos os registros filtrados, não apenas a página visível. Valores e identificadores originais são preservados no CSV. O intervalo pode atravessar anos, com limite de 60 meses por consulta.

## Cobertura e interpretação

### Indicadores do IBGE

O menu agora abre o **Catálogo ampliado**, com os seguintes atalhos:

- Panorama municipal: escolarização, trabalho, saneamento, ambiente e saúde.
- PIB per capita: série revisada da pesquisa de PIB municipal.
- IDHM: índice municipal do PNUD distribuído pela API do IBGE, com seu ano original.
- Natalidade: número de nascidos vivos ocorridos no ano por residência da mãe (Registro Civil). É contagem de nascimentos, não taxa de natalidade por mil habitantes e não é uma consulta ao SINASC.
- Todas as pesquisas do catálogo: lista dinâmica da API de Pesquisas, com seleção de qualquer pesquisa e dos indicadores, incluindo a opção de consultar todos os indicadores da pesquisa escolhida. Não significa consultar automaticamente todas as bases do IBGE nem todas as tabelas SIDRA. Algumas pesquisas não possuem recorte municipal.

Os resultados permitem exibir o último período de cada indicador, todos os anos ou anos selecionados, além de buscar pelo nome. Fontes, notas, unidades e multiplicadores acompanham os valores. Não some totais e subdivisões. O valor é exibido na escala original: o multiplicador é informado em coluna separada, sem aplicação automática.

O panorama pode conter séries antigas ou encerradas. Para PIB per capita, prefira o atalho da série revisada. A fonte e o ano devem ser consultados individualmente; ano de publicação não é ano de referência.

Os códigos especiais de 14 dígitos iniciados em 9999999999999 são preservados e identificados como códigos especiais, sem interpretação como quantidade nem substituição por zero. Não foi atribuído significado específico a cada código.

A opção **Censo e PIB (SIDRA)** preserva as consultas da versão anterior:

No menu lateral, escolha **Indicadores do IBGE**. Selecione um município de São Paulo, o conjunto de indicadores e um ou mais anos disponíveis; clique em **Consultar IBGE**. O padrão é Cosmópolis e o último ano da tabela escolhida.

- População residente, área e densidade: Censo 2022, tabela SIDRA 4714. Não são estimativas atuais de população.
- PIB municipal a preços correntes: tabela SIDRA 5938, variável 37. A unidade retornada é Mil Reais e é exibida sem alterar a escala.
- Os anos disponíveis são obtidos diretamente do IBGE. O período mensal de receitas e despesas não se aplica a esses indicadores.
- A tabela preserva sinais especiais da fonte; eles não são convertidos para zero.
- Dados reais do Censo 2022 e do PIB de 2022/2023 de Cosmópolis foram testados nesta atualização.
- Fontes: https://servicodados.ibge.gov.br/api/docs/localidades e https://sidra.ibge.gov.br/tabela/4714 e https://sidra.ibge.gov.br/tabela/5938.

### Receitas e despesas

- Fonte: https://transparencia.tce.sp.gov.br/apis
- Atende municípios jurisdicionados ao TCE-SP; não é uma consulta nacional nem uma conexão direta ao sistema da prefeitura.
- Receitas: todas as fontes e órgãos disponíveis na resposta, antes dos filtros de tela.
- Despesas: valores agrupados pela movimentação original da API. Empenhos, liquidações, pagamentos, reforços e anulações não são somados em um total único e não são tratados como saldo líquido.
- O painel informa falhas e meses sem registros. Resultado vazio não comprova arrecadação ou despesa zero. Um retorno com registros também não comprova completude contábil.
- A documentação publicada ainda menciona exercícios antigos. Receitas de Cosmópolis de janeiro a março de 2026 foram verificadas na API durante esta atualização (170, 172 e 178 registros, respectivamente). Outros municípios e períodos dependem da disponibilidade do serviço.
- Valores inválidos geram falha no respectivo mês, em vez de serem convertidos silenciosamente para zero.
- A tabela de detalhes exibe moeda como texto; sua ordenação por valor na interface é textual.

### Segurança pública (SSP-SP)

Menu próprio, separado do IBGE. Selecione cidade e intervalo MM/AAAA. A consulta usa os endpoints públicos que alimentam o portal da SSP-SP e não exige login. Inclui homicídios e furtos por padrão; outros indicadores do grupo de ocorrências criminais podem ser selecionados.

- Fonte: https://www.ssp.sp.gov.br/estatistica/dados-mensais
- As ocorrências e os números de vítimas são indicadores diferentes. Totais e subcategorias também se sobrepõem. Não há um total geral somando naturezas.
- Valores após o limite mensal indicado no campo `publicado` da resposta são exibidos como não publicados, nunca como zero.
- As somas são somente dos meses publicados, com a contagem de meses para evidenciar períodos incompletos.
- A integração depende dos endpoints usados pelo portal, que podem mudar; falhas são informadas na tela.
- Testado com dados reais de Cosmópolis em 2026, incluindo identificação de meses ainda não publicados.

## Arquivos

- app.py: interface Streamlit.
- api.py: consultas HTTP, validação do período e valores.
- ibge.py: cliente das APIs de localidades e indicadores do IBGE.
- painel_ibge.py: interface de seleção e visualização dos indicadores.
- catalogo_ibge.py: catálogo ampliado e atalhos de indicadores.
- seguranca.py: consultas públicas à SSP-SP.
- painel_seguranca.py: interface dos dados criminais.
- requirements.txt: dependências.

## Atualizar no GitHub

Envie todos os arquivos .py, requirements.txt e LEIA-ME.md desta pasta, substituindo os arquivos anteriores. Inclua os novos catalogo_ibge.py, seguranca.py e painel_seguranca.py na mesma pasta de app.py. Não envie __pycache__, work ou arquivos de teste. Se já publicou no Streamlit Community Cloud, salve as alterações na mesma branch usada pela implantação.

Nenhum dado fictício é apresentado como resultado. A aplicação consulta os meses sequencialmente e mantém resultados parciais com aviso se o serviço falhar.
