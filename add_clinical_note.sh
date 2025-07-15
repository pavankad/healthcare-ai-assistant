#!/bin/bash

# Script to add a clinical note via API
# This will trigger the real-time UI update when the clinical notes tab is active

# Configuration
PATIENT_ID=13  # Change this to the patient ID you want to add a note to
BASE_URL="http://localhost:5000"
CURRENT_DATE=$(date +%Y-%m-%d)

echo "🏥 Adding Clinical Note via API..."
echo "Patient ID: $PATIENT_ID"
echo "Date: $CURRENT_DATE"
echo ""

# Add a clinical note
curl -X POST \
  "$BASE_URL/api/patients/$PATIENT_ID/clinical-notes" \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_cookie_here" \
  -d "{
    \"date\": \"$CURRENT_DATE\",
    \"provider\": \"Dr. API Test\",
    \"type\": \"Progress Note\",
    \"note\": \"Patient shows good progress. API test note added at $(date). Vital signs stable. Continue current treatment plan.\"
  }" \
  | python3 -m json.tool

echo ""
echo "✅ Clinical note added!"
echo "💡 If you have the clinical notes tab open in the EMR UI, you should see the note appear within 500ms!"
