import json
import hashlib
import paho.mqtt.client as mqtt
from web3 import Web3

# 1. Configuración obtenida desde Remix IDE / Ganache
CONTRACT_ADDRESS = "0x8aB8C9fC793Df1aa2D288944b3937C58Fe52DF08"
NODE_RPC_URL = "http://127.0.0.1:8545"  # Usar 8545 o 7545 según Ganache CLI o GUI

# ABI del Contrato Inteligente (Solidity)
CONTRACT_ABI = json.loads("""[
  {
    "anonymous": false,
    "inputs": [
      { "indexed": true, "internalType": "string", "name": "idEvento", "type": "string" },
      { "indexed": false, "internalType": "uint256", "name": "timestamp", "type": "uint256" },
      { "indexed": false, "internalType": "uint256", "name": "magnitud", "type": "uint256" },
      { "indexed": false, "internalType": "string", "name": "hashContenido", "type": "string" },
      { "indexed": false, "internalType": "address", "name": "registrador", "type": "address" }
    ],
    "name": "AlertaRegistrada",
    "type": "event"
  },
  {
    "inputs": [{ "internalType": "string", "name": "_id", "type": "string" }],
    "name": "existeAlerta",
    "outputs": [{ "internalType": "bool", "name": "", "type": "bool" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [{ "internalType": "uint256", "name": "_limite", "type": "uint256" }],
    "name": "getAlertasPaginadas",
    "outputs": [
      {
        "components": [
          { "internalType": "string", "name": "idEvento", "type": "string" },
          { "internalType": "uint256", "name": "timestamp", "type": "uint256" },
          { "internalType": "uint256", "name": "magnitud", "type": "uint256" },
          { "internalType": "string", "name": "hashContenido", "type": "string" },
          { "internalType": "address", "name": "registrador", "type": "address" },
          { "internalType": "bool", "name": "existe", "type": "bool" }
        ],
        "internalType": "struct AlertAudit.Alerta[]",
        "name": "",
        "type": "tuple[]"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "getTotalAlertas",
    "outputs": [{ "internalType": "uint256", "name": "", "type": "uint256" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [{ "internalType": "uint256", "name": "", "type": "uint256" }],
    "name": "historialAlertas",
    "outputs": [
      { "internalType": "string", "name": "idEvento", "type": "string" },
      { "internalType": "uint256", "name": "timestamp", "type": "uint256" },
      { "internalType": "uint256", "name": "magnitud", "type": "uint256" },
      { "internalType": "string", "name": "hashContenido", "type": "string" },
      { "internalType": "address", "name": "registrador", "type": "address" },
      { "internalType": "bool", "name": "existe", "type": "bool" }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [{ "internalType": "string", "name": "_id", "type": "string" }],
    "name": "obtenerAlertaPorId",
    "outputs": [
      { "internalType": "string", "name": "idEvento", "type": "string" },
      { "internalType": "uint256", "name": "timestamp", "type": "uint256" },
      { "internalType": "uint256", "name": "magnitud", "type": "uint256" },
      { "internalType": "string", "name": "hashContenido", "type": "string" },
      { "internalType": "address", "name": "registrador", "type": "address" }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      { "internalType": "string", "name": "_id", "type": "string" },
      { "internalType": "uint256", "name": "_timestamp", "type": "uint256" },
      { "internalType": "uint256", "name": "_magnitud", "type": "uint256" },
      { "internalType": "string", "name": "_hash", "type": "string" }
    ],
    "name": "registrarAlerta",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
]""")

# 2. Conexión con el nodo Web3 local (Ganache)
w3 = Web3(Web3.HTTPProvider(NODE_RPC_URL))
if not w3.is_connected():
    print(f"[ERROR WEB3] No se pudo conectar al nodo RPC en {NODE_RPC_URL}. Revisa Ganache.")
    exit(1)

contract_address_checksum = Web3.to_checksum_address(CONTRACT_ADDRESS)
contract = w3.eth.contract(address=contract_address_checksum, abi=CONTRACT_ABI)
account = w3.eth.accounts[0]  # Utiliza la primera cuenta disponible en Ganache

print(f"[WEB3] Conectado exitosamente. Cuenta emisora: {account}")

def registrar_en_blockchain(evento_id, timestamp, magnitud, payload_raw):
    try:
        # 1. Comprobación previa On-Chain para evitar duplicados y ahorro de gas
        ya_existe = contract.functions.existeAlerta(str(evento_id)).call()
        if ya_existe:
            print(f"[BLOCKCHAIN] La alerta '{evento_id}' ya está registrada On-Chain. Omitiendo duplicado.")
            return

        # 2. Generación del Hash SHA-256 del JSON original para garantizar auditoría
        hash_contenido = hashlib.sha256(payload_raw.encode('utf-8')).hexdigest()
        
        # Conversión de magnitud flotante a entero uint256 (ej: 5.8 -> 58)
        mag_int = int(round(float(magnitud) * 10))

        print(f"[BLOCKCHAIN] Enviando transacción para la alerta '{evento_id}'...")

        # 3. Envío y minado de la transacción
        tx_hash = contract.functions.registrarAlerta(
            str(evento_id),
            int(timestamp),
            mag_int,
            hash_contenido
        ).transact({'from': account})

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"[BLOCKCHAIN] Alerta registrada On-Chain exitosamente")
        print(f"   ├─ Evento ID: {evento_id}")
        print(f"   ├─ Magnitud (x10): {mag_int}")
        print(f"   ├─ Hash SHA-256: {hash_contenido}")
        print(f"   ├─ Tx Hash: {receipt.transactionHash.hex()}")
        print(f"   └─ Bloque N°: {receipt.blockNumber}\n")

    except Exception as e:
        print(f"[BLOCKCHAIN] Error al registrar la alerta '{evento_id}': {e}\n")

# Callbacks para Paho MQTT
def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("[MQTT BLOCKCHAIN] Conectado con éxito al Broker MQTT.")
        client.publish("estado/subscriber", payload="online", qos=1, retain=True)
        # Suscribirse con QoS 2 para capturar todas las publicaciones del árbol 'terremotos/#'
        client.subscribe("terremotos/#", qos=2)
        print("[MQTT BLOCKCHAIN] Escuchando en el tópico wildcard 'terremotos/#'...\n")
    else:
        print(f"[MQTT BLOCKCHAIN] Error de conexión. Código: {reason_code}")

def on_message(client, userdata, msg):
    topic = msg.topic
    raw_payload = msg.payload.decode('utf-8')

    try:
        print(f"[MQTT RECIBIDO] Topic: '{topic}'")
        data = json.loads(raw_payload)

        # Extracción y normalización de atributos del evento
        evento_id = data.get("id") or data.get("idEvento")
        timestamp = data.get("tiempo") or data.get("timestamp") or 0
        magnitud = data.get("magnitud") or data.get("magnitude") or 0.0

        if not evento_id:
            print("[MQTT BLOCKCHAIN] Omitiendo mensaje: No contiene una clave 'id' válida.\n")
            return

        registrar_en_blockchain(evento_id, timestamp, magnitud, raw_payload)

    except json.JSONDecodeError:
        print(f"[MQTT BLOCKCHAIN] Se recibió un mensaje no-JSON en '{topic}': {raw_payload}\n")
    except Exception as e:
        print(f"[MQTT BLOCKCHAIN] Error procesando el mensaje: {e}\n")

# 3. Inicialización del cliente MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "blockchain_audit_consumer", clean_session=False)
client.will_set("estado/subscriber", payload="offline", qos=1, retain=True)
client.on_connect = on_connect
client.on_message = on_message

print("[BLOCKCHAIN CONSUMER] Iniciando servicio de auditoría Web3...")

try:
    client.connect("127.0.0.1", 1883, 60)
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[BLOCKCHAIN CONSUMER] Servicio detenido manualmente.")
    client.publish("estado/subscriber", payload="offline", qos=1, retain=True)
    client.loop_stop()
    client.disconnect()
