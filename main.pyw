from __future__ import barry_as_FLUFL
from glob import glob
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO
from flaskwebgui import FlaskUI
import time
import socket
import struct

from numpy import True_

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

threadServidor = None
ipServer ="Direccion: " + str(socket.gethostbyname(socket.gethostname()))
status = "No conectado"
servidorEncendido = False
progre = 0
received_bytes = 0
filesize = 0

@app.route("/")
def home():  
    return render_template('index.html')

@app.route("/recibir")
def recibir():  
    global status
    return render_template('recibir.html', ipServer = ipServer, servidorEncendido = servidorEncendido, status = status, progre = progre)

@app.route("/enviar")
def enviar():  
    return render_template('enviar.html')

def receive_file_size(sck: socket.socket):
    # Esta función se asegura de que se reciban los bytes
    # que indican el tamaño del archivo que será enviado,
    # que es codificado por el cliente vía struct.pack(),
    # función la cual genera una secuencia de bytes que
    # representan el tamaño del archivo.
    fmt = "<Q"
    expected_bytes = struct.calcsize(fmt)
    received_bytes = 0
    stream = bytes()
    while received_bytes < expected_bytes:
        chunk = sck.recv(expected_bytes - received_bytes)
        stream += chunk
        received_bytes += len(chunk)
    filesize = struct.unpack(fmt, stream)[0]
    return filesize
def receive_file(sck: socket.socket, filename):
    global received_bytes
    global filesize
    # Leer primero del socket la cantidad de 
    # bytes que se recibirán del archivo.
    filesize = receive_file_size(sck)
    threadEmit = threading.Thread(target=enviarStatusActual)
    # Abrir un nuevo archivo en donde guardar
    # los datos recibidos.
    with open(filename, "wb") as f:
        received_bytes = 0
        threadEmit.start()
        # Recibir los datos del archivo en bloques de
        # 1024 bytes hasta llegar a la cantidad de
        # bytes total informada por el cliente.
        while received_bytes < filesize:
            chunk = sck.recv(1024)
            if chunk:
                f.write(chunk)
                received_bytes += len(chunk)
                

def enviarStatusActual():
    global received_bytes
    global filesize
    while True:
        time.sleep(1)
        socketio.emit("status", str(round(received_bytes/1000000, 2))+"Megabites")
        socketio.emit("progre",str(round((received_bytes*100)/filesize, 2))+"%")
        if received_bytes >= filesize:
            time.sleep(1)
            filesize = 0
            received_bytes = 0
            break
 
def encenderServer():
    global status
    global socketio
    respuestas = ["Esperando al cliente...","Recibiendo archivo...", "conectado.", "Archivo recibido.", "Conexión cerrada."]
    while True:
        with socket.create_server(('localhost', 6190)) as server:
            # espera
            status = respuestas[0]
            time.sleep(1)
            print(status)
            socketio.emit("status",status)
            
            #aceptacion
            conn, address = server.accept()
            status = f"{address[0]}:{address[1]} conectado."
            print(f"{address[0]}:{address[1]} conectado.")
            socketio.emit("status",f"{address[0]}:{address[1]} conectado.")

            # recibiendo
            status = respuestas[1]
            print(status)
            socketio.emit("status",status)
            filename  = conn.recv(1024).decode("UTF-8")
            receive_file(conn, filename)
            
            # recibido
            status = respuestas[3]
            print(respuestas[3])
            socketio.emit("status",respuestas[3])
            
            # conexion cerrada
            status = respuestas[4]
            print(status)
            socketio.emit("status",status)

def cambiarStatus():
    global status
    status = "bond"
    socketio.emit("status",status)
    print(status)

@socketio.on("newFile")
def newFile(e):
    print(e)

if __name__ == '__main__':
    threadServidor = threading.Thread(target=encenderServer)
    threadServidor.start()
    FlaskUI(app, socketio=socketio, start_server="flask-socketio").run()
    #c = threading.Thread(target=socketio.run(app))
    #c.start()
    
    
    