#include <Arduino.h>
#include <DHT.h>

// ======================
// CONFIGURACAO DOS PINOS
// ======================

#define PINO_DHT 12
#define DHTTYPE DHT22

#define BOTAO_N 23
#define BOTAO_P 22
#define BOTAO_K 21

#define LDR_PIN 34

#define RELE_PIN 25

// ======================
// PARAMETROS DA CULTURA: FEIJAO
// ======================

const float UMIDADE_INICIO = 40.0;  // abaixo disso a irrigacao comeca (%)
const float UMIDADE_PARADA = 50.0;  // a partir disso a irrigacao para (%)

const float PH_MINIMO = 5.5;        // faixa de pH adequada ao feijoeiro
const float PH_MAXIMO = 6.5;

const int ADC_MAXIMO = 4095;        // ADC de 12 bits do ESP32

// ======================
// TEMPOS (em milissegundos)
// ======================

const unsigned long INTERVALO_LEITURA = 2000; // DHT22 exige >= 2 s entre leituras
const unsigned long TEMPO_DEBOUNCE    = 50;   // filtra o "quique" mecanico do botao

DHT dht(PINO_DHT, DHTTYPE);

// ======================
// BOTOES NPK EM MODO TOGGLE
// Cada clique inverte o estado do nutriente:
// AUSENTE -> PRESENTE -> AUSENTE ...
// O valor continua sendo "tudo ou nada" (true/false).
// ======================

struct BotaoToggle {
  uint8_t pino;
  const char* nome;
  bool estado;            // true = nutriente PRESENTE
  int  nivelEstavel;      // ultimo nivel confirmado apos o debounce
  int  ultimaLeitura;     // ultima leitura bruta do pino
  unsigned long tempoMudanca;
};

BotaoToggle botoes[] = {
  { BOTAO_N, "N", false, HIGH, HIGH, 0 },
  { BOTAO_P, "P", false, HIGH, HIGH, 0 },
  { BOTAO_K, "K", false, HIGH, HIGH, 0 }
};

const int NUM_BOTOES = sizeof(botoes) / sizeof(botoes[0]);

unsigned long ultimoCiclo = 0;

// Estado da bomba guardado entre ciclos (necessario para a histerese)
bool bombaLigada = false;

// Retorna true quando o botao acabou de ser pressionado
// (borda de descida confirmada), invertendo seu estado.
bool atualizarBotao(BotaoToggle &b) {
  int leitura = digitalRead(b.pino);

  if (leitura != b.ultimaLeitura) {
    b.ultimaLeitura = leitura;
    b.tempoMudanca = millis();
  }

  if ((millis() - b.tempoMudanca) >= TEMPO_DEBOUNCE && leitura != b.nivelEstavel) {
    b.nivelEstavel = leitura;
    if (leitura == LOW) {        // INPUT_PULLUP: LOW = botao apertado
      b.estado = !b.estado;
      return true;
    }
  }
  return false;
}

// ======================
// CONVERSAO LDR -> pH (0 a 14)
// No modulo LDR do Wokwi, mais luz = menor tensao em AO.
// A escala foi invertida para que mais luz (slider para a direita)
// signifique pH maior, deixando a simulacao mais intuitiva.
// ======================

float lerPH(int valorLDR) {
  return (ADC_MAXIMO - valorLDR) * 14.0 / ADC_MAXIMO;
}

// ======================
// CICLO DE LEITURA E DECISAO
// ======================

void executarCiclo() {

  bool nitrogenio = botoes[0].estado;
  bool fosforo    = botoes[1].estado;
  bool potassio   = botoes[2].estado;

  // ======================
  // LEITURA DA UMIDADE
  // ======================

  float umidade = dht.readHumidity();

  if (isnan(umidade)) {
    Serial.println("Erro ao ler DHT22 - bomba desligada por seguranca");
    bombaLigada = false;
    digitalWrite(RELE_PIN, LOW);
    return;
  }

  // ======================
  // LEITURA DO LDR (PH)
  // ======================

  int   valorLDR   = analogRead(LDR_PIN);
  float ph         = lerPH(valorLDR);
  bool  phAdequado = (ph >= PH_MINIMO && ph <= PH_MAXIMO);

  // ======================
  // REGRA DA IRRIGACAO (com histerese)
  // - Liga  : NPK presente, pH adequado e umidade < UMIDADE_INICIO
  // - Desliga: umidade >= UMIDADE_PARADA, ou NPK/pH deixam de
  //            estar adequados
  // - Entre os dois limites a bomba mantem o estado anterior.
  // ======================

  bool soloAdequado = nitrogenio && fosforo && potassio && phAdequado;
  const char* motivo;

  if (!soloAdequado) {
    bombaLigada = false;
    motivo = "nutrientes ou pH fora do adequado";
  } else if (!bombaLigada && umidade < UMIDADE_INICIO) {
    bombaLigada = true;
    motivo = "umidade abaixo do limite de inicio";
  } else if (bombaLigada && umidade >= UMIDADE_PARADA) {
    bombaLigada = false;
    motivo = "umidade atingiu o limite de parada";
  } else {
    motivo = bombaLigada ? "irrigando ate atingir o limite de parada"
                         : "umidade suficiente";
  }

  // ======================
  // CONTROLE DO RELE
  // ======================

  digitalWrite(RELE_PIN, bombaLigada ? HIGH : LOW);

  // ======================
  // MONITOR SERIAL
  // ======================

  Serial.println("--------------------------------");

  Serial.print("N: ");
  Serial.println(nitrogenio ? "PRESENTE" : "AUSENTE");

  Serial.print("P: ");
  Serial.println(fosforo ? "PRESENTE" : "AUSENTE");

  Serial.print("K: ");
  Serial.println(potassio ? "PRESENTE" : "AUSENTE");

  Serial.print("Umidade: ");
  Serial.print(umidade);
  Serial.print("% (inicia < ");
  Serial.print(UMIDADE_INICIO);
  Serial.print("%, para >= ");
  Serial.print(UMIDADE_PARADA);
  Serial.println("%)");

  Serial.print("LDR: ");
  Serial.print(valorLDR);
  Serial.print(" -> pH: ");
  Serial.print(ph, 2);
  Serial.print(" (adequado: ");
  Serial.print(PH_MINIMO, 1);
  Serial.print(" a ");
  Serial.print(PH_MAXIMO, 1);
  Serial.println(")");

  Serial.print("pH adequado: ");
  Serial.println(phAdequado ? "SIM" : "NAO");

  Serial.println(bombaLigada ? ">>> BOMBA LIGADA <<<" : ">>> BOMBA DESLIGADA <<<");
  Serial.print("Motivo: ");
  Serial.println(motivo);
}

void setup() {

  Serial.begin(115200);

  dht.begin();

  for (int i = 0; i < NUM_BOTOES; i++) {
    pinMode(botoes[i].pino, INPUT_PULLUP);
  }

  pinMode(RELE_PIN, OUTPUT);
  digitalWrite(RELE_PIN, LOW);

  Serial.println();
  Serial.println("=================================");
  Serial.println("FARMTECH SOLUTIONS");
  Serial.println("Sistema Inteligente de Irrigacao");
  Serial.println("Cultura: FEIJAO");
  Serial.println("=================================");
  Serial.println("Clique em N, P ou K para alternar PRESENTE/AUSENTE");
}

void loop() {

  // Os botoes sao verificados a cada volta do loop (sem delay),
  // entao nenhum clique e perdido.
  bool houveMudanca = false;

  for (int i = 0; i < NUM_BOTOES; i++) {
    if (atualizarBotao(botoes[i])) {
      houveMudanca = true;
      Serial.print("[BOTAO] ");
      Serial.print(botoes[i].nome);
      Serial.print(" -> ");
      Serial.println(botoes[i].estado ? "PRESENTE" : "AUSENTE");
    }
  }

  // Reavalia a irrigacao a cada 2 s ou imediatamente apos um clique.
  // (A biblioteca DHT devolve a ultima leitura se chamada antes de 2 s.)
  if (houveMudanca || millis() - ultimoCiclo >= INTERVALO_LEITURA) {
    ultimoCiclo = millis();
    executarCiclo();
  }
}
