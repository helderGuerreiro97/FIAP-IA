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

DHT dht(PINO_DHT, DHTTYPE);

void setup() {

  Serial.begin(115200);

  dht.begin();

  pinMode(BOTAO_N, INPUT_PULLUP);
  pinMode(BOTAO_P, INPUT_PULLUP);
  pinMode(BOTAO_K, INPUT_PULLUP);

  pinMode(RELE_PIN, OUTPUT);

  digitalWrite(RELE_PIN, LOW);

  Serial.println();
  Serial.println("=================================");
  Serial.println("FARMTECH SOLUTIONS");
  Serial.println("Sistema Inteligente de Irrigacao");
  Serial.println("=================================");
}

void loop() {

  // ======================
  // LEITURA DOS BOTOES NPK
  // ======================

  bool nitrogenio = (digitalRead(BOTAO_N) == LOW);
  bool fosforo    = (digitalRead(BOTAO_P) == LOW);
  bool potassio   = (digitalRead(BOTAO_K) == LOW);

  // ======================
  // LEITURA DA UMIDADE
  // ======================

  float umidade = dht.readHumidity();

  if (isnan(umidade)) {
    Serial.println("Erro ao ler DHT22");
    delay(2000);
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

  bool irrigar = false;

  if (
      nitrogenio &&
      fosforo &&
      potassio &&
      umidade < 40 &&
      phAdequado
     )
  {
    irrigar = true;
  }

  // ======================
  // CONTROLE DO RELE
  // ======================

  if (irrigar) {
    digitalWrite(RELE_PIN, HIGH);
  } else {
    digitalWrite(RELE_PIN, LOW);
  }

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

  if (irrigar) {
    Serial.println(">>> BOMBA LIGADA <<<");
  } else {
    Serial.println(">>> BOMBA DESLIGADA <<<");
  }

  delay(2000);
}