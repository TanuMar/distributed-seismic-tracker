import sys
import json
import sqlite3
import paho.mqtt.client as mqtt

# Recibir la región por argumento en la terminal (python sqlite_consumer.py europe)
# Si no se pasa argumento, actúa como nodo global por defecto
REGION_SHARD = sys.argv[1].lower() if len(sys.argv) > 1 else "global"
DB_NAME = f"terremotos_{REGION_SHARD}.db"

# Inicializar BD SQLite para este Shard
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

# Habilitar el modo WAL (Write-Ahead Logging) para soportar accesos concurrentes de lectura/escritura
cursor.execute("PRAGMA journal_mode=WAL;")
cursor.execute("PRAGMA synchronous=NORMAL;")

cursor.execute('''
    CREATE TABLE IF NOT EXISTS eventos (
        id TEXT PRIMARY KEY,
        lugar TEXT,
        magnitud REAL,
        longitud REAL,
        latitud REAL,
        profundidad REAL,
        tiempo INTEGER
    )
''')
conn.commit()

# Callbacks para MQTT
def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"[{REGION_SHARD.upper()} DB CONSUMER] Conectado con éxito al Broker MQTT.")
        
        # Publicar estado 'online' con retain=True para este Shard específico
        client.publish("estado/subscriber", payload="online", qos=1, retain=True)
        
        # Definir y suscribir al tópico correspondiente según el Shard
        if REGION_SHARD == "global":
            topic = "terremotos/#"
        else:
            topic = f"terremotos/{REGION_SHARD}/#"
        
        client.subscribe(topic, qos=2)
        print(f"[{REGION_SHARD.upper()} DB CONSUMER] Escuchando en el tópico: '{topic}'...\n")
    else:
        print(f"[{REGION_SHARD.upper()} DB CONSUMER] Error de conexión. Código: {reason_code}")

def on_message(client, userdata, msg):
    topic = msg.topic
    raw_payload = msg.payload.decode('utf-8')

    try:
        data = json.loads(raw_payload)
        
        # Extracción segura de coordenadas
        coordenadas = data.get("coordenadas", [0, 0, 0])
        profundidad = coordenadas[2] if len(coordenadas) > 2 else 0.0

        cursor.execute(
            "INSERT OR IGNORE INTO eventos VALUES (?, ?, ?, ?, ?, ?, ?)",
            (data["id"], data["lugar"], data["magnitud"], coordenadas[0], coordenadas[1], profundidad, data["tiempo"])
        )
        conn.commit()
        print(f"[{REGION_SHARD.upper()} DB] Guardado evento '{data['id']}' ({data['lugar']})")

    except json.JSONDecodeError:
        print(f"[{REGION_SHARD.upper()} DB ERROR] Se recibió un mensaje no-JSON en '{topic}': {raw_payload}\n")
    except KeyError as e:
        print(f"[{REGION_SHARD.upper()} DB ERROR] Clave faltante en el JSON recibido: {e}\n")
    except Exception as e:
        print(f"[{REGION_SHARD.upper()} DB ERROR] Error al guardar en base de datos: {e}\n")

# Inicialización del cliente MQTT
client_id = f"db_consumer_{REGION_SHARD}"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id, clean_session=False)

# Configuración de Last Will & Testament (LWT) para notificar caídas inesperadas
client.will_set("estado/subscriber", payload="offline", qos=1, retain=True)

client.on_connect = on_connect
client.on_message = on_message

print(f"[{REGION_SHARD.upper()} DB CONSUMER] Iniciando servicio de persistencia Off-Chain...")

try:
    client.connect("127.0.0.1", 1883, 60)
    client.loop_forever()
except KeyboardInterrupt:
    print(f"\n[{REGION_SHARD.upper()} DB CONSUMER] Servicio detenido manualmente.")
    client.publish("estado/subscriber", payload="offline", qos=1, retain=True)
    client.loop_stop()
    client.disconnect()
    conn.close()
    print(f"[{REGION_SHARD.upper()} DB CONSUMER] Conexión cerrada y base de datos desconectada correctamente.")
