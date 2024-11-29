import socket
import threading
import paho.mqtt.client as mqtt

# MQTT broker setup
broker = "test.mosquitto.org"  # Public MQTT broker
port = 1883

# Dictionary untuk menyimpan data klien dan saluran
clients = {}  # Menyimpan data klien dalam format {client_socket: {'name': name, 'channel': channel}}
channels = {} # Menyimpan daftar klien di setiap channel {channel_name: [client_sockets]}

def broadcast(message, channel, sender_name, client=None):
    """
    Fungsi untuk mengirim pesan ke semua klien dalam channel tertentu.
    :param message: Pesan yang akan dikirim
    :param channel: Nama channel target
    :param sender_name: Nama pengirim pesan
    :param client: Klien pengirim pesan (opsional, untuk tidak mengirim balik ke pengirim)
    """
    if channel in channels:
        for c in channels[channel]:
            if c != client:  # Only send to others in the same channel agar pengirim tidak menerima ulang pesan yang ia kirim.
                try:
                    c.send(f"{sender_name}: {message}".encode('utf-8'))
                except:
                    remove_client(c)
#KOMUNIKASI 1 ON 1
def send_private_message(sender_name, target_name, message):
    """Send a private message from sender to target if target exists."""
    target_client = None
    sender_client = None  # Socket pengirim
    for client, info in clients.items():
        if info['name'] == target_name:  # Cari penerima pesan
            target_client = client
        if info['name'] == sender_name:  # Cari pengirim pesan
            sender_client = client
    if target_client:
        try:
            target_client.send(f"Private from {sender_name}: {message}".encode('utf-8'))
        except:
            remove_client(target_client)
    else:
        # Jika penerima tidak ditemukan, beri tahu pengirim
        if sender_client:
            sender_client.send(f"Penerima '{target_name}' tidak tersedia atau tidak terhubung.".encode('utf-8'))
        print(f"{sender_name} attempted to message {target_name}, but they are not connected.")

def handle_client(client, name):
    """Handle communication with a single client."""
    current_channel = clients[client]['channel']
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if message:
                # MENU JOIN CHANEL
                if message.startswith("/join/"):
                    # Menggunakan substring untuk mengambil nama channel
                    new_channel = message[6:]  # Ambil substring setelah "/join "
                    if current_channel:
                        leave_channel(client, current_channel, name)
                    join_channel(client, new_channel, name)
                    current_channel = new_channel  # Update local channel after joining
                # MENU LEAVE CHANEL
                elif message == "/leave":
                    if current_channel:
                        leave_channel(client, current_channel, name)
                        current_channel = None  # Update local channel to None
                        client.send("Anda telah keluar dari saluran.".encode('utf-8'))
                    else:
                        client.send("Anda tidak berada di saluran mana pun.".encode('utf-8'))
                # MENU PRIVATE MESSAGE DENGAN MULTITHREAD
                elif message.startswith("/msg/"):
                    # Menggunakan substring untuk memotong "/msg/" dan mengambil target dan pesan
                    message_parts = message[5:]  # Mengambil semua karakter setelah "/msg/"
                    target_name_end = message_parts.find("/")
                    if target_name_end != -1:
                        target_name = message_parts[:target_name_end]  # Substring nama target
                        private_msg = message_parts[target_name_end+1:]  # Substring pesan pribadi
                        send_private_message(name, target_name, private_msg)
                    else:
                        client.send("Format pesan pribadi salah. Gunakan /msg/<nama_client>/<pesan>".encode('utf-8'))
                # Mengirim pesan ke channel
                elif ':' in message:
                    channel, msg = message.split(':', 1)
                    msg = msg.strip()
                    
                    # Ensure client is in the correct channel before broadcasting
                    if clients[client]['channel'] == channel:
                        print(f"Pesan diterima di saluran {channel} dari {name}: {msg}")
                        broadcast(msg, channel, name, client)
                        mqtt_client.publish(f"chatroom/{channel}", f"{name}: {msg}")
                    else:
                        client.send("Anda tidak berada di saluran tersebut.".encode('utf-8'))
                else:
                    print(f"Format pesan salah dari {name}.")
            else:
                remove_client(client)
                break
        except Exception as e:
            print(f"Error: {e}")
            continue


def remove_client(client):
    """
    Fungsi untuk menghapus klien dari daftar ketika klien keluar
    + memberikan notifikasi kepada anggota channel.
    :param client: Socket klien
    """
    if client in clients:
        client_info = clients.pop(client)  # Hapus klien dari dictionary
        channel = client_info['channel']  # Ambil channel klien
        name = client_info['name']  # Ambil nama klien

        if channel in channels and client in channels[channel]:
            channels[channel].remove(client)  # Hapus klien dari channel
            # Broadcast notifikasi kepada anggota channel lain
            broadcast(f"{name} telah keluar dari saluran {channel}.", channel, "Server")

        print(f"Klien {name} telah terputus.")  # Log aktivitas klien

    client.close()  # Tutup koneksi socket


def join_channel(client, channel, name):
    """
    Fungsi untuk menambahkan klien ke channel tertentu.
    :param client: Socket klien
    :param channel: Nama channel yang akan dimasuki
    :param name: Nama klien
    """
    if channel not in channels:
        channels[channel] = [] # Jika channel belum ada, buat baru
    channels[channel].append(client) # + client
    clients[client]['channel'] = channel  # Update client's channel info
    broadcast(f"{name} telah bergabung dengan saluran {channel}.", channel, "Server", client)
    client.send(f"Anda telah bergabung dengan saluran {channel}.".encode('utf-8'))

def leave_channel(client, channel, name):
    """
    Fungsi untuk mengeluarkan klien dari channel tertentu.
    :param client: Socket klien
    :param channel: Nama channel
    :param name: Nama klien
    """
    if channel in channels and client in channels[channel]:
        channels[channel].remove(client)
        clients[client]['channel'] = None  # Update client's channel info to None
        broadcast(f"{name} telah meninggalkan saluran {channel}.", channel, "Server", client)

def start_server():
    """Start the socket server and listen for incoming client connections."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 12345))
    server.listen()

    print("Server telah berjalan dan menunggu koneksi...")

    while True:
        ## Multi threading untuk menerima banyak koneksi
        client, address = server.accept()
        print(f"Terhubung dengan {str(address)}")

        # Loop untuk memastikan nama client unique
        while True:
            ## Multi thread mengelola Nama Pengguna (Username):
            client.send("Masukkan nama Anda: ".encode('utf-8'))
            name = client.recv(1024).decode('utf-8')

            # Check kondisi apakah nama client unique
            if any(info['name'] == name for info in clients.values()):
                client.send("Nama sudah dipakai, silakan pilih nama lain.".encode('utf-8'))
            #Apabila unique akan disimpan ke clients = {}
            else:
                clients[client] = {'name': name, 'channel': None}  # Save client with unique name
                client.send("Nama diterima. Selamat datang!".encode('utf-8'))
                break

        client.send("Masukkan saluran untuk bergabung: ".encode('utf-8'))
        channel = client.recv(1024).decode('utf-8')

        join_channel(client, channel, name)

        client.send(f"Selamat datang di saluran {channel}! Silahkan mulai percakapan.".encode('utf-8'))

        thread = threading.Thread(target=handle_client, args=(client, name))
        thread.start()

# --- MQTT PART ---
def on_mqtt_message(client, userdata, message):
    """Handle incoming messages from the MQTT broker."""
    decoded_message = message.payload.decode('utf-8')
    topic = message.topic.split('/')[-1]  # Extract channel name from topic
    print(f"Received from MQTT on channel {topic}: {decoded_message}")
    
    # Only broadcast the message to clients in the corresponding channel
    if topic in channels:
        broadcast(decoded_message, topic, "MQTT")

def start_mqtt_client():
    """Start the MQTT client."""
    global mqtt_client
    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_mqtt_message
    mqtt_client.connect(broker, port)
    
    # Subscribe to a separate MQTT topic for each channel
    for channel in channels:
        mqtt_client.subscribe(f"chatroom/{channel}")
    
    mqtt_client.loop_start()

if __name__ == "__main__":
    # Start the MQTT client in the background
    start_mqtt_client()

    # Start the socket server
    start_server()
