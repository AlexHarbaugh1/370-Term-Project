import socket
import threading

clients = {}  # Map of connection objects to usernames

def update_user_list():
    """Broadcast the current active user list to all clients."""
    user_list = ','.join(clients.values())
    message = "[USERS]" + user_list
    for client in clients:
        try:
            client.sendall(message.encode())
        except:
            pass

def handle_client(conn, addr):
    try:
        # Receive username upon connection
        username = conn.recv(1024).decode()
        clients[conn] = username
        print(f"{username} joined the chat from {addr}")

        broadcast(f"{username} has joined the chat!", conn)
        update_user_list()

        while True:
            data = conn.recv(1024)
            if not data:
                break
            decoded = data.decode()
            # Handle typing notifications separately
            if decoded == "[TYPING]":
                broadcast(f"[TYPING]{username}", conn)
                continue
            # Handle exit command
            if decoded.lower() == "exit":
                break
            message = f"{username}: {decoded}"
            print(message)
            broadcast(message, conn)
    except Exception as e:
        print("Error:", e)
    finally:
        print(f"{username} disconnected.")
        broadcast(f"{username} has left the chat.", conn)
        del clients[conn]
        update_user_list()
        conn.close()

def broadcast(message, sender_conn):
    """Send the message to all clients except the sender."""
    for client in clients:
        if client != sender_conn:
            try:
                client.sendall(message.encode())
            except:
                pass

def start_server(host='127.0.0.1', port=65432):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)  # Support multiple connections

    print(f"Server listening on {host}:{port}...")

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()
