import pyqrcode
from pyzbar import pyzbar
import cv2
import json

from passlib.hash import sha256_crypt


def decoder(img_path):
    img = cv2.imread(img_path)
    barcodes = pyzbar.decode(img)
    for barcode in barcodes:
        barcodeData = barcode.data.decode("utf-8")
    return json.loads(barcodeData)

def generate_qr(data):
    id = data['id']
    data = json.dumps(data)
    url = pyqrcode.create(data)
    url.png(f'static/qr/batch-{id}.png',scale=20)
    print("Printing QR code")
