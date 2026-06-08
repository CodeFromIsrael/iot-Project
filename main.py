#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h> 

// ===== WIFI =====
const char* ssid = "Dragondex";
const char* password = "testando";

// ===== TELEGRAM =====
String BOT_TOKEN = "8659967301:AAGkw0dkal2mRnroGONz6nEcr0UYv_lajxg";
String CHAT_ID = "1674707575";

// ===== BOTÃO =====
#define BOTAO 26
bool botaoAnterior = HIGH;

// ===== MPU6050 =====
const int MPU_ADDR = 0x68; 
// Sensibilidade: Quanto MENOR esse número, mais sensível fica (dispara mais fácil)
const float LIMITE_MOVIMENTO_BRUSCO = 1.5; 

// Pinos I2C do ESP32
#define I2C_SDA 21
#define I2C_SCL 22

unsigned long ultimoDisparoMpu = 0;
const unsigned long INTERVALO_DISPARO = 6000; // Evita encher o Telegram de spam (espera 6 segundos)

// =========================
// ENVIAR TELEGRAM
// =========================
bool enviarMensagem(String mensagem){
  if(WiFi.status() != WL_CONNECTED){
    Serial.println("WiFi desconectado");
    return false;
  }

  HTTPClient http;
  String url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage?chat_id=" + CHAT_ID + "&text=";

  for(int i=0; i<mensagem.length(); i++){
    if(mensagem[i]==' ') url += "%20";
    else url += mensagem[i];
  }

  http.begin(url);
  int codigo = http.GET();
  http.end();

  Serial.print("HTTP: ");
  Serial.println(codigo);

  return (codigo == 200);
}

// =========================
// SETUP
// =========================
void setup(){
  Serial.begin(115200);
  delay(500);
  Serial.println("ESP iniciado");

  pinMode(BOTAO, INPUT_PULLUP);

  // Inicializa o sensor MPU6050
  Wire.begin(I2C_SDA, I2C_SCL); 
  delay(100);
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B); 
  Wire.write(0);    
  Wire.endTransmission(true);
  Serial.println("MPU6050 Configurado");

  // Sua conexão WiFi original que funciona perfeitamente
  Serial.println("Conectando WiFi");
  WiFi.begin(ssid, password);

  while(WiFi.status() != WL_CONNECTED){
    delay(1000);
    Serial.println(".");
  }

  Serial.println("WiFi conectado");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  bool ok = enviarMensagem("ESP conectado com sucesso");
  if(ok) Serial.println("Telegram conectado");
  else Serial.println("Erro Telegram");
}

// =========================
// LOOP
// =========================
void loop(){
  // --- LÓGICA DO BOTÃO ---
  bool estadoBotao = digitalRead(BOTAO);

  if(estadoBotao == LOW && botaoAnterior == HIGH){
    Serial.println("Botao apertado");
    
    // MUDANÇA DA MENSAGEM DO BOTÃO AQUI:
    bool ok = enviarMensagem("botão pressionado: Estou precisando de ajuda ajuda requisitada");
    
    if(ok) Serial.println("Mensagem enviada");
    else Serial.println("Falha envio");
    delay(500);
  }
  botaoAnterior = estadoBotao;

  // --- LÓGICA DO MPU6050 (MOVIMENTO BRUSCO) ---
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B); 
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 6, true); 

  if(Wire.available() == 6) {
    int16_t rawX = Wire.read() << 8 | Wire.read();
    int16_t rawY = Wire.read() << 8 | Wire.read();
    int16_t rawZ = Wire.read() << 8 | Wire.read();

    // Converte os valores brutos para G (Gravidade)
    float ax = rawX / 16384.0;
    float ay = rawY / 16384.0;
    float az = rawZ / 16384.0;

    // Calcula a força total atuando no sensor (vetor resultante)
    float aceleracaoTotal = sqrt(ax*ax + ay*ay + az*az);
    
    // Subtrai 1.0 (que é a gravidade natural da Terra quando parado)
    float movimento = abs(aceleracaoTotal - 1.0);

    // Se o movimento for maior que o limite e o tempo de segurança passou
    if(movimento > LIMITE_MOVIMENTO_BRUSCO && (millis() - ultimoDisparoMpu > INTERVALO_DISPARO)) {
      ultimoDisparoMpu = millis(); // Reseta o temporizador
      
      Serial.print("Movimento detectado! Forca: ");
      Serial.println(movimento);
      
      // Envia o alerta para o Telegram
      bool okMpu = enviarMensagem("Alerta: Movimento brusco detectado!");
      if(okMpu) Serial.println("Mensagem de movimento enviada");
      else Serial.println("Falha envio MPU");
    }
  }

  delay(30); // Pausa curta para não estressar o processador
}