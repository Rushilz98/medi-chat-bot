import os
import re
import joblib
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify
import requests
import json
from dotenv import load_dotenv
import logging

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ======================
# 🔑 CONFIGURATION
# ======================
# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Medical model paths
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Data')
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'disease_prediction_model.joblib')

# ======================
# 🩺 MEDICAL MODEL SETUP
# ======================
try:
    # Load training data
    training = pd.read_csv(os.path.join(BASE_DIR, 'Training.csv'))
    cols = training.columns[:-1].tolist()

    def normalize_symptom(s):
        return re.sub(r'[^a-z0-9]', '', s.lower().strip())

    normalized_symptoms = [normalize_symptom(col) for col in cols]

    # Load model and encoder
    model_data = joblib.load(MODEL_PATH)
    medical_model = model_data['model']
    label_encoder = model_data['label_encoder']

    logger.info("✅ Medical model loaded successfully")

except Exception as e:
    logger.error(f"❌ ERROR loading medical model: {str(e)}")
    logger.error("1. Verify 'Data/Training.csv' exists")
    logger.error("2. Verify 'models/disease_prediction_model.joblib' exists")
    raise

# ======================
# 💬 CHAT API CONFIG
# ======================
CHAT_MODEL = "openai/gpt-oss-20b:free"
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:5000",
    "X-Title": "MediChat Assistant"
}

# ======================
# 🩺 MEDICAL FUNCTIONALITY
# ======================
def extract_symptoms(user_input):
    """Improved symptom extraction with better matching"""
    if not user_input or not isinstance(user_input, str):
        return []
    
    normalized_input = normalize_symptom(user_input)
    found_symptoms = []
    
    # Direct matching (most reliable)
    for symptom, norm_symptom in zip(cols, normalized_symptoms):
        if norm_symptom in normalized_input:
            found_symptoms.append(symptom)
    
    # N-gram fallback for compound terms
    if not found_symptoms:
        words = re.findall(r'[a-z0-9]+', user_input.lower())
        for n in range(3, 0, -1):
            for i in range(len(words) - n + 1):
                phrase = ''.join(words[i:i+n])
                for symptom, norm_symptom in zip(cols, normalized_symptoms):
                    if norm_symptom == phrase:
                        found_symptoms.append(symptom)
                        break
    
    return list(set(found_symptoms))

def predict_disease(symptoms):
    """Use YOUR model to predict disease from symptoms"""
    if not symptoms:
        return None
    
    # Create symptom vector (EXACTLY as your original code)
    symptom_vector = [1 if col in symptoms else 0 for col in cols]
    
    # Make prediction with YOUR model
    prediction = medical_model.predict([symptom_vector])
    return label_encoder.inverse_transform(prediction)[0]

# ======================
# 🌐 FLASK ROUTES
# ======================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '').strip()
    
    if not user_message:
        return jsonify({"response": "Please enter a message!"})
    
    logger.info(f"Received message: {user_message}")
    
    # STEP 1: Strict medical term detection
    symptoms = extract_symptoms(user_message)
    
    # STEP 2: Enhanced medical keyword check (more precise)
    medical_keywords = [
        'symptom', 'symptoms', 'sick', 'pain', 'fever', 'disease', 'diseases',
        'ill', 'illness', 'ache', 'aches', 'diagnose', 'diagnosis', 'doctor',
        'hospital', 'cough', 'headache', 'migraine', 'rash', 'vomit', 'nausea',
        'dizzy', 'tired', 'fatigue', 'hurt', 'medical', 'condition', 'treatment',
        'prescription', 'medication', 'allergy', 'allergic', 'infection', 'virus',
        
        # Symptom terms without underscores
        'skin rash', 'nodal skin eruptions', 'continuous sneezing', 'shivering', 'chills',
        'joint pain', 'stomach pain', 'acidity', 'ulcers on tongue', 'muscle wasting',
        'vomiting', 'burning micturition', 'spotting urination', 'weight gain', 'anxiety',
        'cold hands and feets', 'mood swings', 'weight loss', 'restlessness', 'lethargy',
        'patches in throat', 'irregular sugar level', 'high fever', 'sunken eyes',
        'breathlessness', 'sweating', 'dehydration', 'indigestion', 'yellowish skin',
        'dark urine', 'loss of appetite', 'pain behind the eyes', 'back pain',
        'constipation', 'abdominal pain', 'diarrhoea', 'mild fever', 'yellow urine',
        'yellowing of eyes', 'acute liver failure', 'fluid overload', 'swelling of stomach',
        'swelled lymph nodes', 'malaise', 'blurred and distorted vision', 'phlegm',
        'throat irritation', 'redness of eyes', 'sinus pressure', 'runny nose', 'congestion',
        'chest pain', 'weakness in limbs', 'fast heart rate', 'pain during bowel movements',
        'pain in anal region', 'bloody stool', 'irritation in anus', 'neck pain', 'dizziness',
        'cramps', 'bruising', 'obesity', 'swollen legs', 'swollen blood vessels',
        'puffy face and eyes', 'enlarged thyroid', 'brittle nails', 'swollen extremeties',
        'excessive hunger', 'extra marital contacts', 'drying and tingling lips',
        'slurred speech', 'knee pain', 'hip joint pain', 'muscle weakness', 'stiff neck',
        'swelling joints', 'movement stiffness', 'spinning movements', 'loss of balance',
        'unsteadiness', 'weakness of one body side', 'loss of smell', 'bladder discomfort',
        'foul smell of urine', 'continuous feel of urine', 'passage of gases',
        'internal itching', 'toxic look (typhos)', 'depression', 'irritability',
        'muscle pain', 'altered sensorium', 'red spots over body', 'belly pain',
        'abnormal menstruation', 'dischromic patches', 'watering from eyes',
        'increased appetite', 'polyuria', 'family history', 'mucoid sputum',
        'rusty sputum', 'lack of concentration', 'visual disturbances',
        'receiving blood transfusion', 'receiving unsterile injections', 'coma',
        'stomach bleeding', 'distention of abdomen', 'history of alcohol consumption',
        'blood in sputum', 'prominent veins on calf', 'palpitations', 'painful walking',
        'pus filled pimples', 'blackheads', 'scurring', 'skin peeling', 'silver like dusting',
        'small dents in nails', 'inflammatory nails', 'blister', 'red sore around nose',
        'yellow crust ooze'
    ]

    # Check if any medical keyword appears as a whole word
    has_medical_term = False
    user_words = re.findall(r'\b\w+\b', user_message.lower())
    for word in user_words:
        if word in medical_keywords:
            has_medical_term = True
            break
    
    # STEP 3: STRICT MEDICAL DECISION LOGIC
    if symptoms or has_medical_term:
        # Always use YOUR medical model when medical terms are detected
        disease = predict_disease(symptoms)
        
        if disease:
            logger.info(f"Medical analysis: symptoms={symptoms}, disease={disease}")
            
            response = (
                f"🔍 **Symptom Analysis**\n\n"
                f"**Reported symptoms**: {', '.join(symptoms) if symptoms else 'detected from context'}\n\n"
                f"**Possible condition**: {disease}\n\n"
                "⚠️ **Important**: This is not a medical diagnosis. "
                "Consult a healthcare professional for accurate assessment."
            )
            return jsonify({
                "response": response,
                "mode": "medical",
                "symptoms": symptoms,
                "disease": disease
            })
    
    # STEP 4: CHAT MODE - Only for NON-MEDICAL conversations
    system_prompt = (
        "You are MediChat, a professional medical information assistant. "
        "You do not have personal experiences or feelings. "
        "Keep responses concise, professional, and medically relevant. "
        "Do not discuss personal topics like pets, family, or your own experiences. "
        "If asked about yourself, state that you are a medical AI assistant."
    )
    
    payload = {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    }

    try:
        # FIX: Removed extra space in the URL
        api_response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=HEADERS,
            json=payload,  # Use json= instead of data=json.dumps()
            timeout=15  # Add timeout to prevent hanging
        )
        api_response.raise_for_status()
        
        result = api_response.json()
        assistant_reply = result["choices"][0]["message"]["content"].strip()
        
        # Additional filtering to ensure professionalism
        if any(word in assistant_reply.lower() for word in ['my dog', 'my cat', 'my pet', 'my name is']):
            assistant_reply = (
                "I'm a medical information assistant focused on health topics. "
                "How can I help with your health concerns today?"
            )
            
        logger.info("Chat response generated successfully")
        return jsonify({
            "response": assistant_reply,
            "mode": "chat"
        })
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error with OpenRouter API: {str(e)}")
        assistant_reply = (
            "I'm a medical information assistant. How can I help with your health concerns today?\n\n"
            "Note: Chat service is temporarily unavailable, but medical analysis is fully functional."
        )
    except (KeyError, TypeError, IndexError) as e:
        logger.error(f"API response parsing error: {str(e)}")
        assistant_reply = (
            "I'm experiencing technical difficulties with the chat service.\n\n"
            "You can still get medical analysis by describing your symptoms."
        )
    except Exception as e:
        logger.exception("Unexpected error in chat API")
        assistant_reply = (
            "I'm experiencing technical difficulties.\n\n"
            "You can still get medical analysis by describing your symptoms."
        )

    return jsonify({
        "response": assistant_reply,
        "mode": "chat"
    })

# ======================
# 🚀 START APPLICATION
# ======================
if __name__ == '__main__':
    logger.info("\n" + "="*50)
    logger.info("🚀 MediChat Professional Assistant is starting locally...")
    logger.info(f"Medical model: {os.path.basename(MODEL_PATH)}")
    logger.info(f"Chat API: {'ACTIVE' if OPENROUTER_API_KEY else 'INACTIVE (no API key)'}")
    logger.info("="*50)
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
