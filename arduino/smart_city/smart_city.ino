#include "DHT.h"

// ===== SENSOR LDR E ILUMINACAO =====

const int ldrPin = A0;
const int ledPin = 9;
const int sensorVaga = 3;

int ldrValue = 0;
int threshold = 50;

// ===== SENSOR DHT22 =====

#define DHTPIN 2
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

// ===== CONFIGURACAO =====

void setup() {
  Serial.begin(9600);

  pinMode(ledPin, OUTPUT);
  pinMode(sensorVaga, INPUT);

  dht.begin();
}

// ===== EXECUCAO =====

void loop() {

  // LEITURA DE LUMINOSIDADE

  ldrValue = analogRead(ldrPin);

  bool posteLigado = (ldrValue < threshold);

  if (posteLigado) {
    digitalWrite(ledPin, HIGH);
  } else {
    digitalWrite(ledPin, LOW);
  }

  // LEITURA DE TEMPERATURA E UMIDADE

  float temperatura = dht.readTemperature();
  float umidade = dht.readHumidity();

  // LEITURA DA VAGA

  int estadoVaga = digitalRead(sensorVaga);

  bool vagaOcupada = (estadoVaga == LOW);

  // ===== ENVIO DOS DADOS EM JSON =====

  Serial.print("{");

  Serial.print("\"ldr\":");
  Serial.print(ldrValue);

  Serial.print(",\"poste\":\"");
  Serial.print(posteLigado ? "ligado" : "desligado");
  Serial.print("\"");

  Serial.print(",\"vaga\":\"");
  Serial.print(vagaOcupada ? "ocupada" : "livre");
  Serial.print("\"");

  Serial.print(",\"temperatura\":");

  if (isnan(temperatura)) {
    Serial.print("null");
  } else {
    Serial.print(temperatura / 31.5, 2);
  }

  Serial.print(",\"umidade\":");

  if (isnan(umidade)) {
    Serial.print("null");
  } else {
    Serial.print(umidade / 20, 2);
  }

  Serial.println("}");

  delay(2000);
}
