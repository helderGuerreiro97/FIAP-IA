#include <DHT.h>

// Configuração dos Pinos
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

  Serial.println("=================================");
  Serial.println("FARMTECH SOLUTIONS");
  Serial.println("Sistema Inteligente de Irrigacao");
  Serial.println("=================================");
}

void loop() {

//Leitura dos Botões

  bool nitrogenio = (digitalRead(BOTAO_N) == LOW);
  bool fosforo    = (digitalRead(BOTAO_P) == LOW);
  bool potassio   = (digitalRead(BOTAO_K) == LOW);

  // LEITURA DHT22

  float umidade = dht.readHumidity();

  if (isnan(umidade)) {
    Serial.println("Erro na leitura do DHT22");
    delay(2000);
    return;
  }

  // LEITURA LDR (PH)

  int valorLDR = analogRead(LDR_PIN);

  // Faixa simulada de pH adequado
  bool phAdequado = (valorLDR >= 1200 && valorLDR <= 3000);

  // LOGICA DE IRRIGACAO

  bool irrigar = false;

  if (nitrogenio &&
      fosforo &&
      potassio &&
      umidade < 40 &&
      phAdequado) {

    irrigar = true;
  }

  // CONTROLE DO RELE

  if (irrigar) {
    digitalWrite(RELE_PIN, HIGH);
  } else {
    digitalWrite(RELE_PIN, LOW);
  }

  // MONITOR SERIAL

  Serial.println("--------------------------------");

  Serial.print("Nitrogenio (N): ");
  Serial.println(nitrogenio ? "PRESENTE" : "AUSENTE");

  Serial.print("Fosforo (P): ");
  Serial.println(fosforo ? "PRESENTE" : "AUSENTE");

  Serial.print("Potassio (K): ");
  Serial.println(potassio ? "PRESENTE" : "AUSENTE");

  Serial.print("Umidade: ");
  Serial.print(umidade);
  Serial.println(" %");

  Serial.print("LDR (pH): ");
  Serial.println(valorLDR);

  Serial.print("Faixa de pH adequada: ");
  Serial.println(phAdequado ? "SIM" : "NAO");

  if (irrigar) {
    Serial.println("BOMBA LIGADA");
  } else {
    Serial.println("BOMBA DESLIGADA");
  }

  delay(2000);
}