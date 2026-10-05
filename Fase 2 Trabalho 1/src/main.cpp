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
    digitalWrite(RELE_PIN, LOW);
    return;
  }

  // ======================
  // LEITURA DO LDR (PH)
  // ======================

  int valorLDR = analogRead(LDR_PIN);

  // Simulacao de faixa de pH ideal
  bool phAdequado = (valorLDR >= 1200 && valorLDR <= 3000);

  // ======================
  // REGRA DA IRRIGACAO
  // ======================

  bool irrigar = nitrogenio && fosforo && potassio &&
                 umidade < 40 && phAdequado;

  // ======================
  // CONTROLE DO RELE
  // ======================

  digitalWrite(RELE_PIN, irrigar ? HIGH : LOW);

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
  Serial.println("%");

  Serial.print("Valor LDR (pH): ");
  Serial.println(valorLDR);

  Serial.print("pH adequado: ");
  Serial.println(phAdequado ? "SIM" : "NAO");

  Serial.println(irrigar ? ">>> BOMBA LIGADA <<<" : ">>> BOMBA DESLIGADA <<<");
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
