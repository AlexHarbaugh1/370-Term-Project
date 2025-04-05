import socket
import threading

def receive_messages(client_socket):
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            print(f"\n{data.decode()}\n> ", end="")
        except:
            break

def start_client(host='127.0.0.1', port=65432):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # Get username from the user
    username = input("Enter your username: ")
    client_socket.sendall(username.encode())

    print("Connected to chat server. Type messages and press Enter to send.")
    
    # Start receiving messages in a separate thread
    threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()

    while True:
        message = input("> ")
        if message.lower() == 'exit':
            break
        client_socket.sendall(message.encode())

    client_socket.close()

if __name__ == "__main__":
    start_client()
