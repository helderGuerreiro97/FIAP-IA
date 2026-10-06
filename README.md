# FIAP - Faculdade de Informática e Administração Paulista 

<p align="center">
<a href= "https://www.fiap.com.br/"><img src="[assets/logo-fiap.png](https://github.com/helderGuerreiro97/FIAP-IA/blob/Fase2_Trab2/canacontrol-fiap/assets/logo-fiap.png)" alt="FIAP - Faculdade de Informática e Admnistração Paulista" border="0" width=40% height=40%></a>
</p>

<br>

# CanaControl - Monitor de Perdas na Colheita de Cana-de-Açúcar

## Grupo 12

## 👨‍🎓 Integrantes: 
- Almério Samuel Almeida Pinto (RM574304)
- André Felipe Vieira da Silva (RM574808)
- Helder de Melo Guerreiro (RM575318)
- Priscila Fernandes de Carvalho (RM576037)

## 👩‍🏫 Professores:
### Tutor(a) 
- Nome do Tutor
### Coordenador(a)
- Nome do Coordenador


## 📜 Descrição

### O problema

O Brasil é o maior produtor mundial de cana-de-açúcar, mas perde uma parte significativa da produção durante a colheita. Segundo a SOCICANA, as perdas na colheita mecânica podem chegar a **15% da produção**, enquanto na colheita manual raramente passam de **5%**. Para quem produz, isso é dinheiro deixado no campo a cada safra.

O problema é que muitos produtores não medem essas perdas de forma organizada. Sem saber **quanto** se perde, **onde** se perde e **em qual tipo de colheita**, fica difícil decidir o que corrigir: a regulagem das colhedoras, a velocidade de operação, o momento da colheita ou o planejamento de cada talhão.

### A solução

O **CanaControl** é um sistema em Python, executado no terminal, que registra talhões e colheitas e transforma esses registros em informação para a tomada de decisão:

- **Cálculo automático da perda** de cada colheita, em toneladas, em percentual e em reais, comparando a produção esperada (área × produtividade) com a produção colhida.
- **Alertas automáticos** quando a perda passa do limite aceitável para o tipo de colheita: 5% para manual e 15% para mecânica.
- **Ranking de talhões** por prejuízo, para mostrar onde agir primeiro.
- **Comparativo manual × mecânica**, com a perda média e o prejuízo de cada modalidade.
- **Relatórios em arquivo texto** e **backup em JSON**.
- **Persistência em banco Oracle**.

### Inovação

Em vez de apenas armazenar dados, o CanaControl aplica os limites de referência do setor para **classificar cada colheita automaticamente** como OK ou ALERTA. Ele também **prioriza os talhões pelo prejuízo financeiro**, e assim o produtor sabe onde agir primeiro sem precisar dominar os detalhes técnicos da cadeia produtiva. É a mesma lógica das agrotechs: entregar uma ferramenta que facilita o monitoramento.

### Conteúdos aplicados (Capítulos 3 a 6)

| Conteúdo | Onde está no código (`src/canacontrol.py`) |
|---|---|
| **Função** com passagem de parâmetros | `calcular_indicadores(colheita, talhao)`, `ler_float(mensagem, minimo, maximo)`, `montar_ranking()`, `moeda(valor)` |
| **Procedimento** com passagem de parâmetros | `exibir_tabela(cabecalhos, linhas)`, `salvar_json(caminho)`, `titulo(texto)`, `enviar_para_oracle(conexao)` |
| **Lista** | `talhoes` e `colheitas`, além das linhas das tabelas exibidas |
| **Tupla** | `TIPOS_COLHEITA = ("manual", "mecanica")` e `LIMITES_PERDA = (5.0, 15.0)` |
| **Dicionário** | cada talhão e cada colheita; o dicionário `acoes` do menu |
| **Tabela de memória** | `talhoes` e `colheitas` são listas de dicionários usadas em todos os cálculos e relatórios |
| **Arquivo texto** | `gerar_relatorio_txt()` gera o relatório em `relatorios/` |
| **Arquivo JSON** | `salvar_json()` e `carregar_json()` (backup em `dados/canacontrol.json`) |
| **Banco Oracle** | `conectar_oracle()`, `criar_tabelas_oracle()`, `enviar_para_oracle()`, `carregar_do_oracle()` |

### Consistência dos dados de entrada

Todas as entradas do usuário são validadas antes de serem gravadas:

- Números: aceita vírgula ou ponto, recusa texto e valores negativos ou zerados, e aplica limites máximos. A produção colhida, por exemplo, não pode passar do dobro do esperado, o que pega erros de digitação.
- Datas: exige o formato DD/MM/AAAA e recusa datas inválidas ou futuras.
- Tipo de colheita: só aceita os valores da tupla `TIPOS_COLHEITA`.
- Textos: não aceita campos vazios nem nomes de talhão repetidos.
- Opções de menu e confirmações (s/n): repetem a pergunta até receber uma resposta válida.


## 📁 Estrutura de pastas

Dentre os arquivos e pastas presentes na raiz do projeto, definem-se:

- <b>assets</b>: aqui estão os arquivos relacionados a elementos não-estruturados deste repositório, como imagens.

- <b>document</b>: aqui estão todos os documentos do projeto que as atividades poderão pedir. Na subpasta "other" estão um exemplo de relatório gerado pelo sistema (`exemplo_relatorio.txt`) e um exemplo do backup em JSON (`exemplo_dados.json`).

- <b>src</b>: todo o código-fonte do projeto:
  - `canacontrol.py`: o programa completo.
  - `criar_tabelas.sql`: script de criação das tabelas no Oracle.

- <b>requirements.txt</b>: dependências do projeto.

- <b>README.md</b>: arquivo que serve como guia e explicação geral sobre o projeto (o mesmo que você está lendo agora).

## 🔧 Como executar o código

### Pré-requisitos
- Python 3.10 ou superior
- Biblioteca `oracledb`, para a conexão com o Oracle
- Acesso a um banco Oracle (ex.: o servidor da FIAP)

### Passo a passo

1. Clone o repositório:
   ```bash
   git clone <url-deste-repositorio>
   cd <nome-do-repositorio>
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure o acesso ao Oracle no início de `src/canacontrol.py`:
   ```python
   ORACLE_USUARIO = "RM000000"      # seu usuário
   ORACLE_SENHA = "sua_senha"       # sua senha
   ORACLE_DSN = "oracle.fiap.com.br:1521/ORCL"
   ```

4. Execute o programa:
   ```bash
   cd src
   python canacontrol.py
   ```

5. Na primeira execução, entre no menu **11 → 1** para criar as tabelas no Oracle. Também é possível rodar o `criar_tabelas.sql` direto no SQL Developer.

### Menu do sistema

```
 1. Cadastrar talhão
 2. Registrar colheita
 3. Listar talhões
 4. Listar colheitas
 5. Relatório de perdas e alertas
 6. Ranking de talhões por prejuízo
 7. Comparativo manual x mecânica
 8. Salvar dados em JSON
 9. Carregar dados do JSON
10. Gerar relatório TXT
11. Banco de dados Oracle
 0. Sair
```

Sem o Oracle configurado, o sistema funciona normalmente com a tabela de memória e os arquivos JSON/TXT; apenas o menu 11 avisa que não há conexão.


## 🗃 Histórico de lançamentos

* 1.0.0 - 05/10/2026
    * Versão de entrega: cadastro de talhões e colheitas, cálculo de perdas, alertas, ranking, comparativo, arquivos TXT/JSON e integração com Oracle.

## 📋 Licença

<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1"><p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/"><a property="dct:title" rel="cc:attributionURL" href="https://github.com/agodoi/template">MODELO GIT FIAP</a> por <a rel="cc:attributionURL dct:creator" property="cc:attributionName" href="https://fiap.com.br">Fiap</a> está licenciado sobre <a href="http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">Attribution 4.0 International</a>.</p>
