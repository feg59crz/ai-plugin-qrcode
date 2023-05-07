import os
import hashlib
import time
from waitress import serve
from flask import Flask, request, jsonify, send_from_directory, send_file

import qrcode
import io

app = Flask(__name__)
IMAGE_DIRECTORY = 'images/'
BASE_URL = 'http://qrcode.feg59crz.repl.co/'


@app.route('/qr_code', methods=['GET'])
def qr_code():
  data = request.args.get('data')
  qr = qrcode.QRCode(version=1, box_size=10, border=5)
  qr.add_data(data)
  qr.make(fit=True)
  img = qr.make_image(fill_color="black", back_color="white")
  img_io = io.BytesIO()
  img.save(img_io, 'PNG')
  img_io.seek(0)

  # Generate MD5 hash of the image
  md5_hash = hashlib.md5(img_io.getvalue()).hexdigest()

  # Save the image to disk with its MD5 hash as the filename
  image_path = os.path.join(IMAGE_DIRECTORY, md5_hash + '.png')
  with open(image_path, 'wb') as f:
    f.write(img_io.getvalue())

  # Return the URL path of the image
  url_path = BASE_URL + IMAGE_DIRECTORY + md5_hash + '.png'
  response = {'url': url_path}
  return jsonify(response)


@app.route('/images/<path:filename>', methods=['GET'])
def serve_image(filename):
  return send_from_directory(IMAGE_DIRECTORY, filename)


def delete_image(filename):
  # Delete the image file
  image_path = os.path.join(IMAGE_DIRECTORY, filename)
  os.remove(image_path)


@app.route('/.well-known/ai-plugin.json')
def serve_ai_plugin():
  return send_from_directory('.',
                             'ai-plugin.json',
                             mimetype='application/json')


@app.route('/.well-known/openapi.yaml')
def serve_openapi_yaml():
  return send_from_directory('.', 'openapi.yaml', mimetype='text/yaml')


@app.route('/.well-known/logo.png')
def serve_logo():
  return send_from_directory('.', 'logo.png', mimetype='image/x-png')


if __name__ == '__main__':
  # Start a separate thread to delete images after 10 minutes
  import threading

  def delete_images():
    while True:
      time.sleep(600)  # 10 minutes
      for filename in os.listdir(IMAGE_DIRECTORY):
        delete_image(filename)

  t = threading.Thread(target=delete_images)
  t.start()

  # Start the server
  serve(app, host="0.0.0.0", port=8080)
