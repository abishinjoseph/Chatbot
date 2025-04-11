import google.generativeai as genai
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import json

# Configure Google Gemini API
api_key = "AIzaSyAwC2KpR0DXzHyG0VDaoEjDm7nvaSuryMM"
genai.configure(api_key=api_key)

# Define generation configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# System instruction for the chatbot
system_instruction = (
    "You are a friendly and knowledgeable Medicare chatbot designed to assist users with basic medical concerns. "
    "You provide medicine recommendations for minor ailments such as headaches, colds, fever, and stomach pain, including the correct dosage and potential side effects. "
    "For severe symptoms (e.g., chest pain, difficulty breathing), advise users to seek medical attention and suggest the appropriate specialist. "
    "Your tone is warm, supportive, and easy to understand, ensuring users feel comfortable while interacting with you. "
    "Always encourage users to consult a doctor for severe or unclear conditions and avoid prescribing restricted medications."
)

# Initialize generative model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

app = Flask(__name__, template_folder='templates')
CORS(app)

# Create directories if they don't exist
if not os.path.exists('templates'):
    os.makedirs('templates')
if not os.path.exists('static'):
    os.makedirs('static')

# Initialize doctors data
doctors_data = {
    "Dr. LEO DAS": "Available",
    "Dr. Smith": "Not Available",
    "Dr. Johnson": "Available",
    "Dr. Williams": "Available"
}

# Store appointments
appointments = []

# Save doctors data to a file
def save_doctors_data():
    with open('static/doctors.json', 'w') as f:
        json.dump(doctors_data, f)

# Load doctors data from file
def load_doctors_data():
    global doctors_data
    try:
        with open('static/doctors.json', 'r') as f:
            doctors_data = json.load(f)
    except FileNotFoundError:
        save_doctors_data()  # Create the file if it doesn't exist

# Save appointments data
def save_appointments():
    with open('static/appointments.json', 'w') as f:
        json.dump(appointments, f)

# Load appointments data
def load_appointments():
    global appointments
    try:
        with open('static/appointments.json', 'r') as f:
            appointments = json.load(f)
    except FileNotFoundError:
        save_appointments()  # Create the file if it doesn't exist

# Initialize data on startup
load_doctors_data()
load_appointments()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user')
def user_portal():
    return render_template('user.html')

@app.route('/admin')
def admin_portal():
    return render_template('admin.html')

@app.route('/appointments')
def view_appointments():
    return render_template('appointments.html')

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.json.get('message')
    try:
        response = model.generate_content([system_instruction, user_input])
        model_response = response.text.strip()
        return jsonify({'response': model_response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_doctors', methods=['GET'])
def get_doctors():
    return jsonify(doctors_data)

@app.route('/update_doctor', methods=['POST'])
def update_doctor():
    data = request.json
    doctor_name = data.get('doctor')
    status = data.get('status')

    if doctor_name and status:
        if status == "REMOVE":
            if doctor_name in doctors_data:
                del doctors_data[doctor_name]
        else:
            doctors_data[doctor_name] = status
        save_doctors_data()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Invalid data'}), 400

@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    data = request.json
    doctor_name = data.get('doctor')

    if doctor_name in doctors_data:
        if doctors_data[doctor_name] == "Available":
            # Add appointment to the list with proper default values
            appointment = {
                'patient_name': data.get('name', 'Not Provided'),
                'patient_email': data.get('email', 'Not Provided'),
                'patient_phone': data.get('phone', 'Not Provided'),
                'appointment_date': data.get('date', 'Not Provided'),
                'appointment_time': data.get('time', 'Not Provided'),
                'symptoms': data.get('symptoms', 'Not Provided'),
                'doctor': doctor_name,
                'status': 'Confirmed'
            }
            appointments.append(appointment)
            save_appointments()
            return jsonify({'success': True, 'message': f'Appointment booked with {doctor_name}'})
        else:
            return jsonify(
                {'success': False, 'message': f'{doctor_name} is not available. Please choose another doctor.'})
    return jsonify({'success': False, 'message': 'Doctor not found'}), 404

@app.route('/get_appointments', methods=['GET'])
def get_appointments():
    # Sanitize appointments data before sending to frontend
    sanitized_appointments = []
    for appt in appointments:
        sanitized_appointment = {
            'patient_name': appt.get('patient_name', 'Not Provided'),
            'patient_email': appt.get('patient_email', 'Not Provided'),
            'patient_phone': appt.get('patient_phone', 'Not Provided'),
            'appointment_date': appt.get('appointment_date', 'Not Provided'),
            'appointment_time': appt.get('appointment_time', 'Not Provided'),
            'symptoms': appt.get('symptoms', 'Not Provided'),
            'doctor': appt.get('doctor', 'Not Provided'),
            'status': appt.get('status', 'Confirmed')
        }
        sanitized_appointments.append(sanitized_appointment)
    return jsonify(sanitized_appointments)

if __name__ == '__main__':
    app.run(debug=True)
