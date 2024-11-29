import socket
import threading

def receive_messages(client):
    """Receive messages from the server and display them."""
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if message:
                print("\n" + message)  # Display the message
            else:
                break
        except:
            print("Terputus dari server.")
            break

def start_client():
    # Membuat socket klien
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Menghubungkan ke server
    client.connect(('10.200.144.48', 12345))  

    # Receive and enter name
    while True:
        message = client.recv(1024).decode('utf-8')
        print(message)
        name = input()
        client.send(name.encode('utf-8')) # Kirim nama ke server

        # Wait for confirmation if the name is unique
        response = client.recv(1024).decode('utf-8')
        if response == "Nama sudah dipakai, silakan pilih nama lain.":
            print(response)  # Jika nama sudah dipakai, ulangi input
        else:
            print(response)
            break

    # Initial channel join
    message = client.recv(1024).decode('utf-8')
    print(message)
    channel = input()
    client.send(channel.encode('utf-8')) # Kirim nama saluran ke server


    # Start a thread to receive messages
    thread = threading.Thread(target=receive_messages, args=(client,))
    thread.start()

    # Loop to send messages
    while True:
        message = input()
        if message.lower() == 'exit':
            client.send("Keluar dari chat.".encode('utf-8'))
            break
        elif message.startswith("/join "):  # Command to change channel
            new_channel = message.split(" ", 1)[1]
            client.send(f"/join {new_channel}".encode('utf-8'))
            channel = new_channel  # Update local channel variable
        elif message == "/leave":  # Command to leave current channel
            client.send("/leave".encode('utf-8'))
            channel = None  #apabila client leave maka channel dibuat none
        
        #KOMUNIKASI 1 ON 1
        elif message.startswith("/msg "):  # Command to send private message
            target_name, private_msg = message.split(" ", 2)[1:]
            client.send(f"/msg {target_name} {private_msg}".encode('utf-8'))
        else:
            #proses untuk memastikan pengiriman pesan dalam channel apakah pengirim benar2 ada di channel
            if channel:
                client.send(f"{channel}: {message}".encode('utf-8'))
                #kondisi apabila tidak ada di channel manapun
            else:
                print("Anda tidak berada di saluran mana pun. Gunakan /join <nama_saluran> untuk bergabung.")

    client.close()

if __name__ == "__main__":
    start_client()
