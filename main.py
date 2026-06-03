import network
import urequests
import time
from machine import Pin, I2C
import math

SSID = "SEU_WIFI"
PASSWORD = "SUA_SENHA"

BOT_TOKEN = "SEU_BOT_TOKEN"
CHAT_ID = "SEU_CHAT_ID"

botao = Pin(14, Pin.IN, Pin.PULL_UP)

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
MPU_ADDR = 0x68

i2c.writeto_mem(MPU_ADDR, 0x6B, b'\x00')

alerta_queda_enviado = False

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(SSID, PASSWORD)

while not wifi.isconnected():
    time.sleep(1)

print("WiFi conectado!")

def enviar_mensagem(mensagem):

    url = (
        f"https://api.telegram.org/bot{BOT_TOKEN}"
        f"/sendMessage?chat_id={CHAT_ID}&text={mensagem}"
    )

    try:
        resposta = urequests.get(url)
        resposta.close()
        print("Mensagem enviada!")

    except Exception as erro:
        print("Erro:", erro)

def ler_acelerometro():

    dados = i2c.readfrom_mem(MPU_ADDR, 0x3B, 6)

    x = int.from_bytes(dados[0:2], 'big', True)
    y = int.from_bytes(dados[2:4], 'big', True)
    z = int.from_bytes(dados[4:6], 'big', True)

    return x, y, z

while True:

    if botao.value() == 0:
        enviar_mensagem("🚨 Botão de emergência acionado!")
        time.sleep(2)

    x, y, z = ler_acelerometro()

    intensidade = math.sqrt(x*x + y*y + z*z)

    if intensidade > 30000 and not alerta_queda_enviado:

        enviar_mensagem("⚠️ Possível queda detectada!")

        alerta_queda_enviado = True

    if intensidade < 18000:
        alerta_queda_enviado = False

    time.sleep(0.2)