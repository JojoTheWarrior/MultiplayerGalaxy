import pygame
import pickle
import random
import socket
import threading
import os
from planet import Planet
import json
from config import SERVER_IP
import time
import math
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
assets_dir = os.path.join(current_dir, 'assets')
fonts_dir = os.path.join(assets_dir, 'fonts')
images_dir = os.path.join(assets_dir, 'images')
background_image_path = os.path.join(images_dir, 'cosmic-background.jpg')
chatbox_font_path = os.path.join(fonts_dir, 'SpaceMono-Bold.ttf')

SEND_INTERVAL = 1 / 60.0
lastSent = time.time()
updateRequired = False

myId = -1
game_state = []

chatbox = []
currentMsg = ""
inTextMode = False

myPlanet = Planet([400, 400], [0, 0], [0, 0], [0, 0, 0], 10)

bumpingCooldown = 0

running = True
# listens for updates from the server
def receive_game_state():
    global myId, game_state, chatbox, myPlanet

    while True:
        try:
            json_data = client.recv(4096).decode('utf-8')

            if not json_data:
                print("Connection closed by the server")
                break

            data = json.loads(json_data)

            myId, game_state, chatbox = data[0], [Planet.from_dict(planet_dict) for planet_dict in data[1]], data[2]
            myPlanet = game_state[myId]
        
        except Exception as e:
            print(f"Error {e}")
            break

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client.connect((SERVER_IP, 5555))
except Exception as e:
    print(f"Unable to connect to the server {e}")
    sys.exit()

pygame.init()
clock = pygame.time.Clock()

info = pygame.display.Info()
W, H = info.current_w, info.current_h
screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
background_image = pygame.image.load(background_image_path)

pygame.display.set_caption("Multiplayer Galaxy")

receive_thread = threading.Thread(target=receive_game_state)
receive_thread.start()

# colors and fonts
font = pygame.font.Font(chatbox_font_path, 40)
chatboxBG = (71, 71, 71)

def tell_server():
    try:
        data = [[planet.to_dict() for planet in game_state], chatbox]
        json_data = json.dumps(data)
        client.send(json_data.encode('utf-8'))
    except Exception as e:
        print(f"Error sending data {e}")

while running:
    # handles events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            updateRequired = True
            # closing acceleration
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                myPlanet.acc[0] = 0
            if event.key in (pygame.K_UP, pygame.K_DOWN):
                myPlanet.acc[1] = 0
            # changing color
            if not inTextMode and event.key == pygame.K_SPACE:
                myPlanet.color = [random.randint(1, 255), random.randint(1, 255), random.randint(1, 255)]
                updateRequired = True
            # reset everyone's position
            if not inTextMode and event.key == pygame.K_r:
                for planet in game_state:
                    planet.pos = [random.randint(0, W), random.randint(0, H)]
                chatbox.insert(0, {'text': f"Positions reset by {myId}", 'id': myId})
                updateRequired = True

            # typing words
            if inTextMode:
                if event.key == pygame.K_RETURN:
                    print("msg sent")
                    chatbox.insert(0, {'text': currentMsg, 'id': myId})
                    currentMsg = ""
                    updateRequired = True
                    inTextMode = False
                elif event.key == pygame.K_BACKSPACE:
                    if len(currentMsg) > 0:
                        currentMsg = currentMsg[:-1]
                elif event.unicode.isprintable():
                    currentMsg += event.unicode
            
            # opening keyboard
            if not inTextMode and event.key == pygame.K_t:
                inTextMode = True
            if inTextMode and event.key == pygame.K_ESCAPE:
                inTextMode = False

        if event.type == pygame.KEYUP:
            updateRequired = True
            # slowing acceleration
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                myPlanet.acc[0] = 1 / myPlanet.radius
            if event.key in (pygame.K_UP, pygame.K_DOWN):
                myPlanet.acc[1] = 1 / myPlanet.radius
        

    keys = pygame.key.get_pressed()

    # changing size
    if keys[pygame.K_UP] and keys[pygame.K_LSHIFT]:
        myPlanet.radius += 1
        updateRequired = True
    if keys[pygame.K_DOWN] and keys[pygame.K_LSHIFT]:
        myPlanet.radius -= 1
        updateRequired = True
    # changing velocity
    if keys[pygame.K_LEFT]:
        myPlanet.vel[0] += -10 / myPlanet.radius
    if keys[pygame.K_RIGHT]:
        myPlanet.vel[0] += 10 / myPlanet.radius
    if keys[pygame.K_UP] and not keys[pygame.K_LSHIFT]:
        myPlanet.vel[1] += -10 / myPlanet.radius
    if keys[pygame.K_DOWN] and not keys[pygame.K_LSHIFT]:
        myPlanet.vel[1] += 10 / myPlanet.radius
    
    myPlanet.radius = max(20, min(myPlanet.radius, 100))

    # bouncing off another planet
    collidingWithOther = -1
    for index, planet in enumerate(game_state):
        if planet == myPlanet:
            continue
        centerDistance = math.sqrt(abs(planet.pos[0]-myPlanet.pos[0])**2 + abs(planet.pos[1]-myPlanet.pos[1])**2)
        if centerDistance <= planet.radius + myPlanet.radius:
            collidingWithOther = index
            
    # updating your position
    for i in range(2):
        if myPlanet.vel[i] < -0.05:
            myPlanet.vel[i] += myPlanet.acc[i]
            updateRequired = True
        if myPlanet.vel[i] > 0.05:
            myPlanet.vel[i] -= myPlanet.acc[i]
            updateRequired = True

        # bouncing off walls
        if (myPlanet.pos[i] <= myPlanet.radius and myPlanet.vel[i] < 0) or (myPlanet.pos[i] >= [W,H][i] - myPlanet.radius and myPlanet.vel[i] > 0):
            myPlanet.vel[i] *= -1
            updateRequired = True
        elif collidingWithOther != -1:
            o = game_state[collidingWithOther]
            m1, m2 = myPlanet.radius ** 2, o.radius ** 2
            myVel = [0 for _ in range(2)]

            myVel = ((m1 - m2) * myPlanet.vel[i] + 2 * m2 * o.vel[i]) / (m1 + m2)
            o.vel[i] = ((m2 - m1) * o.vel[i] + 2 * m1 + myPlanet.vel[i]) / (m1 + m2)
            myPlanet.vel[i] = myVel
            updateRequired = True
            
        myPlanet.vel[i] = max(-200 / myPlanet.radius, min(myPlanet.vel[i], 200 / myPlanet.radius))
        myPlanet.pos[i] += myPlanet.vel[i]

    if updateRequired and time.time() - lastSent >= SEND_INTERVAL:
        updateRequired = False
        lastSent = time.time()
        tell_server()
        
    # draws objects
    screen.fill((0, 0, 0))
    screen.blit(background_image, (0 - 0.5*myPlanet.pos[0], 0 - 0.5*myPlanet.pos[1]))

    pygame.display.set_caption(f"Multiplayer Galaxy {myId}")

    for planet in game_state:
        pygame.draw.circle(screen, tuple(planet.color), planet.pos, planet.radius)

    # draws the chatbox
    if inTextMode:
        pygame.draw.rect(screen, chatboxBG, (10, H-70, W-20, 60))
        text_rect = font.render(currentMsg, True, myPlanet.color)
        screen.blit(text_rect, (10, H-60))
        
        for index, msg in enumerate(chatbox):
            # draw a bg box
            screen.blit(font.render(msg['text'], True, game_state[msg['id']].color), (10, H - 120 - 60*index))
    else:
        for index, msg in enumerate(chatbox):
            # draw a bg box
            screen.blit(font.render(msg['text'], True, game_state[msg['id']].color), (10, H - 120 - 60*index))

    pygame.display.flip()

    clock.tick(60)
    bumpingCooldown = max(0, bumpingCooldown - 1)
    

pygame.quit()
client.close()
sys.exit()