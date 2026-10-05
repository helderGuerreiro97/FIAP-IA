# FarmTech Solutions — Sistema Inteligente de Irrigação com ESP32

**FIAP — Fase 2 — Cap. 1 "Um Mapa do Tesouro" — Grupo 36**

## Integrantes

Almério Samuel Almeida Pinto - RM574304 - [RM574304](https://github.com/RM574304) 
André Felipe Vieira da Silva - RM574808 - [Andrefelipeam](https://github.com/Andrefelipeam) 
Helder de Melo Guerreiro - RM575318 - [helderGuerreiro97](https://github.com/helderGuerreiro97) 

## Vídeo de demonstração

▶️ [Assista no YouTube](COLE_AQUI_O_LINK_DO_VIDEO) *(vídeo não listado, até 5 minutos)*

---

## 1. Objetivo

Simular, na plataforma [Wokwi](https://wokwi.com), um dispositivo baseado em ESP32 que monitora as condições do solo de uma lavoura de **feijão** e decide automaticamente quando ligar e desligar a bomba d'água de irrigação, representada por um módulo relé.

Como o Wokwi não possui sensores agrícolas, foram feitas as substituições didáticas propostas no enunciado:

- Grandeza real - Componente usado na simulação -

Sensores de Nitrogênio (N), Fósforo (P) e Potássio (K) - 3 botões verdes (presente / ausente) 
Sensor de pH do solo - Sensor de luminosidade LDR (valor analógico convertido para pH 0–14) 
Sensor de umidade do solo - DHT22 (mede umidade do ar, usado aqui como umidade do solo) 
Bomba d'água - Módulo relé

## 2. Circuito

![Circuito montado no Wokwi](https://github.com/helderGuerreiro97/FIAP-IA/blob/Fase2_Trab1/circuito-wokwi.png)

### Ligações

Componente Pino do componente - Pino do ESP32 
 Botão N (nitrogênio) - sinal / GND - GPIO 23 / GND 
 Botão P (fósforo) - sinal / GND - GPIO 22 / GND 
 Botão K (potássio) - sinal / GND - GPIO 21 / GND 
 DHT22 - VCC / SDA / GND - 5V / GPIO 12 / GND 
 Módulo LDR - VCC / GND / AO - 3V3 / GND / GPIO 34 (ADC) 
 Módulo relé - VCC / GND / IN - 5V / GND / GPIO 25 

Os botões usam o resistor de *pull-up* interno do ESP32 (`INPUT_PULLUP`), por isso não há resistores externos: o pino fica em nível alto quando o botão está solto e em nível baixo quando é pressionado.

## 3. Cultura escolhida: feijão

O grupo escolheu o feijão (*Phaseolus vulgaris*), cultura de grande importância no Brasil. A escolha define os parâmetros da lógica de irrigação:

- Parâmetro - Valor adotado - Justificativa -

- pH adequado - 5,5 a 6,5 - O feijoeiro se desenvolve melhor em solo levemente ácido. -
- Início da irrigação - umidade < 40% - Limite definido pelo grupo para a simulação. -
- Parada da irrigação - umidade ≥ 50% - Limite superior diferente do inferior para evitar liga/desliga constante. -
- Nutrientes - N, P e K presentes - O grupo optou por exigir os três nutrientes para irrigar. -

> **Observação:** na prática agronômica, o momento de irrigar o feijão é definido pela tensão da água no solo ou pela fração de água disponível consumida, e a irrigação repõe a água até a capacidade de campo (ver Referências). Os valores de 40% e 50% são simplificações didáticas, já que o DHT22 fornece apenas um percentual de umidade. Eles estão definidos como constantes no início do código e podem ser ajustados facilmente.

## 4. Funcionamento e lógica do programa

O código está em [`src/main.cpp`](src/main.cpp) (C++ / framework Arduino).

### 4.1 Botões NPK no modo *toggle*

Os botões do Wokwi são momentâneos, ou seja, só ficam pressionados enquanto o mouse é mantido sobre eles, o que impediria indicar a presença simultânea dos três nutrientes. Por isso, cada botão funciona como um **interruptor**: um clique marca o nutriente como **PRESENTE**, o clique seguinte como **AUSENTE**. O valor continua sendo "tudo ou nada" (`true`/`false`), como pede o enunciado.

Para isso, o programa:

- verifica os botões a cada volta do `loop()`, sem usar `delay()`, para não perder nenhum clique;
- aplica *debounce* de 50 ms, pois o botão simulado reproduz a trepidação mecânica de um botão real;
- inverte o estado apenas na borda de descida (momento em que o botão é pressionado).

### 4.2 Leitura do pH (LDR)

O valor analógico do LDR (0 a 4095, ADC de 12 bits) é convertido para a escala de pH de 0 a 14:

```cpp
pH = (4095 - valorLDR) * 14 / 4095
```

A escala foi invertida para que **mais luz signifique pH maior**, tornando a simulação mais intuitiva. Valores aproximados no slider do Wokwi:

- Iluminação (lux) - pH aproximado -
---------
- 50 - 5,3 (ácido demais) -
- 60 - 5,8 (adequado) -
- 80 - 6,5 (limite superior) -
- 100 - 7,0 (neutro) -

Conforme o enunciado, o pH é ajustado **manualmente** no slider do LDR: ao alterar os níveis de NPK nos botões, o operador ajusta o LDR para representar a mudança que esses nutrientes provocariam no pH do solo.

### 4.3 Leitura da umidade (DHT22)

A umidade é lida a cada 2 segundos, intervalo mínimo recomendado para o DHT22. Em caso de falha de leitura, a bomba é desligada por segurança.

### 4.4 Decisão de irrigação (com histerese)

A bomba usa dois limites de umidade, e não um só. Com um único limite, a bomba ficaria ligando e desligando sempre que a umidade oscilasse em torno dele.

```
SE nutriente ausente OU pH fora de 5,5–6,5:
    DESLIGA a bomba (mesmo que esteja irrigando)
SENÃO SE bomba desligada E umidade < 40%:
    LIGA a bomba
SENÃO SE bomba ligada E umidade >= 50%:
    DESLIGA a bomba
SENÃO:
    mantém o estado atual
```

- Situação - Bomba -
---------
- N, P, K presentes + pH adequado + umidade < 40% - **LIGA** -
- Irrigando e umidade entre 40% e 50% - continua **LIGADA** -
- Umidade atinge 50% - **DESLIGA** -
- Algum nutriente ausente ou pH fora da faixa - **DESLIGA** -
- Falha na leitura do DHT22 - **DESLIGA** -

A cada ciclo, ou imediatamente após um clique em um botão, o Monitor Serial exibe o estado de N, P e K, a umidade, o valor do LDR e o pH calculado, o estado da bomba e o **motivo** da decisão.

Exemplo de saída:

```
--------------------------------
N: PRESENTE
P: PRESENTE
K: PRESENTE
Umidade: 35.50% (inicia < 40.00%, para >= 50.00%)
LDR: 2205 -> pH: 6.46 (adequado: 5.5 a 6.5)
pH adequado: SIM
>>> BOMBA LIGADA <<<
Motivo: umidade abaixo do limite de inicio
```

## 5. Como executar

### Opção 1 — VS Code (usada pelo grupo)

1. Instale as extensões **PlatformIO IDE** e **Wokwi Simulator** no VS Code.
2. Abra a pasta do projeto.
3. Compile com **PlatformIO: Build**. As bibliotecas `DHT sensor library` e `Adafruit Unified Sensor` são baixadas automaticamente, conforme o `platformio.ini`.
4. Abra o `diagram.json` e inicie a simulação com **Wokwi: Start Simulator**.

### Opção 2 — wokwi.com

Crie um projeto ESP32, cole o conteúdo de `diagram.json` e de `src/main.cpp` e adicione a biblioteca **DHT sensor library for ESPx** ou **DHT sensor library** pelo gerenciador de bibliotecas.

## 6. Estrutura do repositório

```
├── src/
│   └── main.cpp          # código C++ do ESP32
├── images/
│   └── circuito-wokwi.png
├── diagram.json          # circuito do Wokwi
├── wokwi.toml            # configuração do simulador no VS Code
├── platformio.ini        # configuração de build e bibliotecas
└── README.md
```

## 7. Limitações da simulação

- O DHT22 mede umidade relativa do ar, usada aqui como substituta da umidade do solo.
- O LDR mede luminosidade; o pH é simulado e ajustado manualmente.
- A presença de nutrientes é binária (presente/ausente), sem medir concentração.
- Os programas opcionais "Ir Além" (integração com API meteorológica e análise em R) não foram implementados nesta entrega.

## Referências

- EMBRAPA. *Critérios de manejo na irrigação do feijoeiro em solo de textura arenosa*. Disponível em: <https://www.alice.cnptia.embrapa.br/alice/bitstream/doc/1021655/1/166173511PB.pdf>
- EMBRAPA Arroz e Feijão. *Manejo da irrigação do feijoeiro com tensiômetro*. Disponível em: <https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/210486/1/comt38.pdf>
- FIAP. *Chamando todas as placas* (Fase 1, Cap. 8).
- Documentação do Wokwi: <https://docs.wokwi.com>
