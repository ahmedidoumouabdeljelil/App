import threading
import time
import  pyrebase
import numpy as np
import tensorflow as tf
from flask import Flask, render_template
from flask_socketio import SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
firebaseConfig = {
    "apiKey": "AIzaSyBjDArp_CvaEjvELFQWd_S1N7dSJW6Kz0o",
    "authDomain": "data-5647b.firebaseapp.com",
    "databaseURL": "https://data-5647b-default-rtdb.europe-west1.firebasedatabase.app",
    "projectId": "data-5647b",
    "storageBucket": "data-5647b.appspot.com",
    "messagingSenderId": "1068830233307",
    "appId": "1:1068830233307:web:02a0f8d39e0cd6cb4b32fe",
    "measurementId": "G-EJ0HL4XT0R"
}
firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()
# Charger le modèle TFLite
interpreter = tf.lite.Interpreter(model_path="model_GRU_3.tflite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def load_data_and_predict():
    while True:
        try:
            data = db.get().val()
            if isinstance(data, dict):  # Assurez-vous que data est un dictionnaire
                courant = data.get('Courant', 0)
                tension = data.get('Tension', 0)
                temperature = data.get('Temperature', 0)   
                input_data = np.array([[courant, tension, temperature]], dtype=np.float32)
                interpreter.set_tensor(input_details[0]['index'], input_data)
                interpreter.invoke()
                output_data = interpreter.get_tensor(output_details[0]['index'])
                soc = output_data[0]
                
                # Émettre l'événement SocketIO avec la prédiction
                socketio.emit('prediction', {'SOC': soc.tolist()})
            else:
                print("Les données récupérées ne sont pas au format attendu :", data)
        except Exception as e:
            print("Erreur lors de la récupération des données ou de la prédiction :", str(e))
        
        time.sleep(5)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    threading.Thread(target=load_data_and_predict).start()
    socketio.run(app, debug=True)
