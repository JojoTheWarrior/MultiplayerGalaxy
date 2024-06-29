import copy
import socket
import pickle
import threading
import random
import json
from config import SERVER_IP
from planet import Planet

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((SERVER_IP, 5555))
server.listen()

clients = []
game_state = []
chatbox = []

def tell_the_world():
    global clients, game_state, chatbox

    for index, c in enumerate(clients):
        if c:
            try:
                data = [index, [planet.to_dict() for planet in game_state], chatbox]
                json_data = json.dumps(data)
                c.sendall(json_data.encode('utf-8'))
            except Exception as e:
                print(f"Error sending data to {index}")
                clients[index] = None


def handle_client(client_socket, id):
    global clients, game_state, chatbox
    print(f"Handling {id}")
    try:
        while True:
            json_data = client_socket.recv(4096).decode('utf-8')
            if not json_data:
                break
            data = json.loads(json_data)
            game_state = [Planet.from_dict(planet_dict) for planet_dict in data[0]]
            chatbox = data[1]
            print(f"received chatbox {chatbox}")
            tell_the_world()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        del clients[id]
        del game_state[id]
        client_socket.close()
        tell_the_world()

# loop to accept clients
while True:
    client_socket, addr = server.accept()

    # now we have someone here
    print(f"Connected to {addr}")

    # permille
    game_state.append(
        Planet(
        [random.randint(1, 800), random.randint(1, 800)],
        [0, 0],
        [0, 0],
        [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)],
        50)
    )

    clients.append(client_socket)

    handle_thread = threading.Thread(target=handle_client, args=(client_socket, len(clients)-1, ))
    handle_thread.start()

    tell_the_world()

