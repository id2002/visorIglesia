import sys
import cv2
import requests
import base64
from io import BytesIO
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer

# URL que muestra la vista HTML con la imagen proyectada por Holyrics
HOLYRICS_VIEW_URL = "http://192.168.18.15:8080/view/standard"

class CameraWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visor Iglesia - Cámara + Holyrics")

        self.image_label = QLabel()
        self.image_label.setStyleSheet("background-color: black;")
        self.text_label = QLabel("")  # Por si quieres mensajes
        self.text_label.setStyleSheet("font-size: 18px; color: white; background-color: black;")

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.text_label)
        self.setLayout(layout)

        # Cámara RTSP
        self.cap = cv2.VideoCapture("rtsp://192.168.18.41:554/live/av0")

        # Timer para actualizar frame de cámara
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(33)  # ≈ 30 fps

        # Timer para verificar si hay imagen desde Holyrics
        self.api_timer = QTimer()
        self.api_timer.timeout.connect(self.check_html_page)
        self.api_timer.start(1000)  # Cada 1 segundo

        self.show_camera = True
        self.last_frame = None

    def update_frame(self):
        if self.show_camera:
            ret, frame = self.cap.read()
            if ret:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
                self.image_label.setPixmap(QPixmap.fromImage(img))
                self.last_frame = img
            else:
                self.text_label.setText("No se pudo leer desde la cámara.")
        else:
            # No mostrar cámara, la imagen ya fue mostrada desde Holyrics
            pass

    def check_html_page(self):
        try:
            response = requests.get(HOLYRICS_VIEW_URL, timeout=2)
            soup = BeautifulSoup(response.text, 'html.parser')

            img_tag = soup.find("img", {"id": "reloader"})
            if img_tag:
                src = img_tag.get("src", "")
                print("Encontrado src:", src[:100])  # Solo los primeros 100 caracteres
                if src.startswith("data:image/jpeg;base64,"):
                    b64_data = src.split(",", 1)[1]
                    img_data = base64.b64decode(b64_data)
                    image = QImage.fromData(img_data)
                    if not image.isNull():
                        self.image_label.setPixmap(QPixmap.fromImage(image))
                        self.text_label.setText("")
                        self.show_camera = False
                        return

            # No hay imagen válida
            self.show_camera = True

        except Exception as e:
            print("Error al consultar Holyrics:", e)
            self.show_camera = True
            self.text_label.setText("Sin conexión a Holyrics")


    def closeEvent(self, event):
        self.cap.release()

# Lanzar aplicación
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraWindow()
    window.show()
    sys.exit(app.exec_())
