import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import socket
import struct
import threading
import time
import os
import configparser
import sqlite3

porcentajeEnviado = 0
porcentajeRecibido = 0
filesize = 0
sended_bytes = 0
received_bytes = 0
filesForSend = []
threadActualizacion = None
config = configparser.ConfigParser()
path = ''
app = None
TransferenciaFacil = None
ui = None
ip = ""
version = "Versión: 1.0.1"

def send_file(sck: socket.socket, filename):
    global filesize
    global sended_bytes
    global threadActualizacion
    global ui
    # Obtener el tamaño del archivo a enviar.
    filesize = os.path.getsize(filename)
    sended_bytes = 0
    
    threadActualizacion = threading.Thread(target=actualizarEstadoEnviado)
    threadActualizacion.setDaemon(True)
    threadActualizacion.start()

    # Informar primero al servidor la cantidad
    # de bytes que serán enviados.
    sck.sendall(struct.pack("<Q", filesize))
    # Enviar el archivo en bloques de 1024 bytes.

    f = open(filename, "rb")
    while read_bytes := f.read(1024):
        sck.sendall(read_bytes)
        sended_bytes += len(read_bytes)
    threadActualizacion = None
    

def actualizarEstadoEnviado():
    global ui
    global filesize
    global sended_bytes
    ui.progressBar.setValue(0)
    while sended_bytes < filesize:
        print(filesize)
        time.sleep(1)
        porcentaje = ((sended_bytes*100)/filesize)
        ui.progressBar.setValue(int(porcentaje))

def connectServerForSend(ip):
    global filesForSend
    socket.setdefaulttimeout(1000)
    print(f"enviando a {ip}")
    for file in filesForSend:
        parts = file.split('/')
        name = parts[len(parts)-1]
        filepath = file.replace('/','\\')
        print(f"enviando {filepath}")
        with socket.create_connection((ip, 6190)) as conn:
            print("Conectado al servidor.")
            print("Enviando archivo...")
            conn.send(name.encode("UTF-8").strip())
            send_file(conn, filepath)
            print("Enviado.")
        print("Conexión cerrada.")


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
    global ui
    global filesize
    global received_bytes
    # Leer primero del socket la cantidad de
    # bytes que se recibirán del archivo.
    filesize = receive_file_size(sck)
    received_bytes = 0
    threading.Thread(target=actualizarEstadoRecibido).start()
    #threadEmit = threading.Thread(target=enviarStatusActual)
    # Abrir un nuevo archivo en donde guardar
    # los datos recibidos.
    with open(filename, "wb") as f:
        # threadEmit.start()
        # Recibir los datos del archivo en bloques de
        # 1024 bytes hasta llegar a la cantidad de
        # bytes total informada por el cliente.
        while received_bytes < filesize:
            chunk = sck.recv(1024)
            if chunk:
                f.write(chunk)
                received_bytes += len(chunk)


def actualizarEstadoRecibido():
    global ui
    global filesize
    global received_bytes
    while received_bytes < filesize:
        time.sleep(1)
        porcentaje = ((received_bytes*100)/filesize)
        ui.progressBarRecibir.setValue(int(porcentaje))


def runServer():
    time.sleep(2)
    global ui
    global ip
    respuestas = ["Esperando al cliente...", "Recibiendo archivo...",
                  "conectado.", "Archivo recibido.", "Conexión cerrada."]
    while True:
        with socket.create_server((ip, 6190)) as server:
            try:
                # espera
                status = respuestas[0]
                ui.progressBarRecibir.setValue(0)
                print(status)
                ui.status.setText("Status: " + status)

                # aceptacion
                conn, address = server.accept()
                status = f"{address[0]} conectado."
                print(f"{address[0]}:{address[1]} conectado.")
                ui.status.setText("Status: " + status)

                # recibiendo
                status = respuestas[1]
                print(status)
                filename = conn.recv(1024).decode("UTF-8")
                receive_file(conn, filename)
                ui.status.setText("Status: " + status)

                # recibido
                status = respuestas[3]
                print(respuestas[3])
                ui.status.setText("Status: " + status)

                # conexion cerrada
                status = respuestas[4]
                print(status)
                ui.status.setText("Status: " + status)
            except ConnectionResetError:
                time.sleep(3)




class Ui_TransferenciaFacil(object):
    def setupUi(self, TransferenciaFacil):
        TransferenciaFacil.setObjectName("TransferenciaFacil")
        TransferenciaFacil.setWindowModality(QtCore.Qt.ApplicationModal)
        TransferenciaFacil.setEnabled(True)
        TransferenciaFacil.resize(500, 320)
        TransferenciaFacil.setFixedSize(TransferenciaFacil.size())
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(
            "./icono.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        TransferenciaFacil.setWindowIcon(icon)
        TransferenciaFacil.setStyleSheet("")
        self.centralwidget = QtWidgets.QWidget(TransferenciaFacil)
        self.centralwidget.setObjectName("centralwidget")
        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setEnabled(True)
        self.tabWidget.setGeometry(QtCore.QRect(10, 10, 480, 251))
        self.tabWidget.setObjectName("tabWidget")
        self.tab_R = QtWidgets.QWidget()
        self.tab_R.setObjectName("tab_R")
        self.progressBarRecibir = QtWidgets.QProgressBar(self.tab_R)
        self.progressBarRecibir.setEnabled(True)
        self.progressBarRecibir.setGeometry(QtCore.QRect(20, 102, 451, 21))
        self.progressBarRecibir.setProperty("value", 0)
        self.progressBarRecibir.setObjectName("progressBarRecibir")
        self.status = QtWidgets.QLabel(self.tab_R)
        self.status.setGeometry(QtCore.QRect(20, 160, 371, 21))
        self.status.setObjectName("status")
        self.direccionEsteEquipo = QtWidgets.QLabel(self.tab_R)
        self.direccionEsteEquipo.setGeometry(QtCore.QRect(20, 190, 361, 16))
        self.direccionEsteEquipo.setObjectName("direccionEsteEquipo")
        self.label_5 = QtWidgets.QLabel(self.tab_R)
        self.label_5.setGeometry(QtCore.QRect(20, 30, 551, 31))
        font = QtGui.QFont()
        font.setFamily("Arial Narrow")
        font.setPointSize(9)
        font.setItalic(True)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")
        self.label_4 = QtWidgets.QLabel(self.tab_R)
        self.label_4.setGeometry(QtCore.QRect(20, 10, 131, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.tabWidget.addTab(self.tab_R, "")
        self.tab_E = QtWidgets.QWidget()
        self.tab_E.setObjectName("tab_E")
        self.btnSeleccionar = QtWidgets.QPushButton(self.tab_E)
        self.btnSeleccionar.setGeometry(QtCore.QRect(20, 150, 121, 21))
        self.btnSeleccionar.setObjectName("btnSeleccionar")
        self.direccionDestinoText = QtWidgets.QLineEdit(self.tab_E)
        # con autoscan cambiar valor de direccionDestinoText de 270 a 191
        self.direccionDestinoText.setGeometry(QtCore.QRect(120, 61, 270, 20))
        self.direccionDestinoText.setObjectName("direccionDestinoText")
        self.label_2 = QtWidgets.QLabel(self.tab_E)
        self.label_2.setGeometry(QtCore.QRect(20, 60, 101, 21))
        self.label_2.setObjectName("label_2")
        self.progressBar = QtWidgets.QProgressBar(self.tab_E)
        self.progressBar.setGeometry(QtCore.QRect(20, 100, 451, 21))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.btnEnviar = QtWidgets.QPushButton(self.tab_E)
        self.btnEnviar.setEnabled(False)
        self.btnEnviar.setGeometry(QtCore.QRect(160, 190, 81, 31))
        self.btnEnviar.setStyleSheet(
            "background-color:rgb(0, 0, 255); color:#FFF;")
        self.btnEnviar.setObjectName("btnEnviar")
        self.nombreArchivoText = QtWidgets.QLineEdit(self.tab_E)
        self.nombreArchivoText.setEnabled(False)
        self.nombreArchivoText.setGeometry(QtCore.QRect(150, 150, 241, 21))
        self.nombreArchivoText.setObjectName("nombreArchivoText")
        #self.pushButton = QtWidgets.QPushButton(self.tab_E)
        #self.pushButton.setGeometry(QtCore.QRect(320, 60, 71, 23))
        #self.pushButton.setObjectName("pushButton")
        self.label = QtWidgets.QLabel(self.tab_E)
        self.label.setGeometry(QtCore.QRect(20, 10, 131, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.label_3 = QtWidgets.QLabel(self.tab_E)
        self.label_3.setGeometry(QtCore.QRect(20, 20, 451, 31))
        font = QtGui.QFont()
        font.setFamily("Arial Narrow")
        font.setPointSize(9)
        font.setItalic(True)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.tabWidget.addTab(self.tab_E, "")
        
        self.versionLabel = QtWidgets.QLabel(self.centralwidget)
        self.versionLabel.setObjectName("Version")
        self.versionLabel.setGeometry(QtCore.QRect(350, 265, 371, 21))
        self.versionLabel.setFont(font)
        
        TransferenciaFacil.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(TransferenciaFacil)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 428, 21))
        self.menubar.setObjectName("menubar")
        TransferenciaFacil.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(TransferenciaFacil)
        self.statusbar.setObjectName("statusbar")
        TransferenciaFacil.setStatusBar(self.statusbar)
        
        self.retranslateUi(TransferenciaFacil)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(TransferenciaFacil)

    def retranslateUi(self, TransferenciaFacil):
        global ip
        global version
        _translate = QtCore.QCoreApplication.translate
        TransferenciaFacil.setWindowTitle(_translate(
            "TransferenciaFacil", "Transferencia Facil"))
        self.status.setText(_translate("TransferenciaFacil", "Status:"))
        self.direccionEsteEquipo.setText(_translate(
            "TransferenciaFacil", "Direccion del equipo: " + ip))
        self.label_5.setText(_translate(
            "TransferenciaFacil", "Utilice esta ventana para recibir archivos. Acá podras ver la direccion de tu equipo"))
        self.label_4.setText(_translate(
            "TransferenciaFacil", "Recibir Archivos"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(
            self.tab_R), _translate("TransferenciaFacil", "Recibir Archivos"))
        self.btnSeleccionar.setText(_translate(
            "TransferenciaFacil", "Seleccionar Archivo"))
        self.label_2.setText(_translate(
            "TransferenciaFacil", "Direccion destino:"))
        self.btnEnviar.setText(_translate("TransferenciaFacil", "Enviar"))
        self.btnEnviar.setDisabled(True)
        #self.pushButton.setText(_translate("TransferenciaFacil", "Autoscan"))
        self.label.setText(_translate(
            "TransferenciaFacil", "Enviar Archivos:"))
        self.label_3.setText(_translate(
            "TransferenciaFacil", "Utilice esta ventana para enviar archivos colocando la direccion destino."))
        self.tabWidget.setTabText(self.tabWidget.indexOf(
            self.tab_E), _translate("TransferenciaFacil", "Enviar Archivos"))
        self.versionLabel.setText(_translate(
            "TransferenciaFacil", version))
        self.btnSeleccionar.clicked.connect(self.pushButtonSeleccionarArchivo)
        self.btnEnviar.clicked.connect(self.enviar)
        
    def pushButtonSeleccionarArchivo(self):
        global filesForSend
        filesForSend = []
        self.btnEnviar.setDisabled(False)        
        filenames = QtWidgets.QFileDialog.getOpenFileNames()
        filesForSend = filenames[0]
        if(len(filenames[0])==0):
            pass
        elif(len(filenames[0])==1):
            partes = filenames[0][0].split('/')
            nombreArchivo = partes[len(partes)-1]
            self.nombreArchivoText.setText(nombreArchivo)
        else:
            self.nombreArchivoText.setText(f"Seleccionados {len(filenames[0])} archivos")

    def enviar(self):
        global filesForSend
        global ui
        if(len(filesForSend)!=0):
            threading.Thread(target=connectServerForSend, args=(self.direccionDestinoText.text(),)).start()
        
    
    def testIP(ip,octatenos):
        s = socket.socket()
        s.settimeout(2)
        try:
            direActual = octatenos[0] + '.' + octatenos[1] + '.' + octatenos[2] + '.' + str(i)
            s.connect((direActual,6190)) 
            print("conectado!")
            print(direActual)
        except Exception as e:
            print(e)
        
    def autoscanear(self):
        global ip
        octatenos = ip.split('.')
        i = 2
        s = socket.socket()
        s.settimeout(2)
        connected = False
        for i in range(253):
            if(str(i)!=octatenos[3] and connected==False and i!=0 and i!=1):
                print(i)
                threading.Thread(target=self.testIP,args=(ip,octatenos)).start()
        s.shutdown(0)
    
    def saveFile(self):
        saveDialog = QtWidgets.QFileDialog.getExistingDirectoryUrl()
        print(saveDialog.url().split('///')[1])


def runGui():
    global app
    global TransferenciaFacil
    global ui
    app = QtWidgets.QApplication(sys.argv)
    TransferenciaFacil = QtWidgets.QMainWindow()
    ui = Ui_TransferenciaFacil()
    ui.setupUi(TransferenciaFacil)

    TransferenciaFacil.show()
    sys.exit(app.exec_())


def stop():
    while True:
        if(TransferenciaFacil.isVisible() == False):
            os._exit(0)
        time.sleep(1)


if __name__ == '__main__':
   
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    path = cur.execute('''select * from config;''').fetchone()
    if(path==None):
        cur.execute("""INSERT INTO config (idConfig, key, value) 
               VALUES (?,?,?);""", (1,"path", str(os.getcwd()))).fetchall()
        con.commit()
        path = cur.execute('''select * from config;''').fetchone()

    print(path)
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = str(s.getsockname()[0])
    threadServidor = threading.Thread(target=runServer, args=())
    threadServidor.start()
    threadGui = threading.Thread(target=runGui, args=())
    threadGui.start()
    threadStop = threading.Thread(target=stop)
    time.sleep(1)
    threadStop.start()
