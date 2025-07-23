import torchxrayvision as xrv
import skimage, torch, torchvision
import openai
import json
import os
from datetime import datetime

# Prepare the image:
img = skimage.io.imread("xray-images/xray1.jpg")
img = xrv.datasets.normalize(img, 255) # convert 8-bit image to [-1024, 1024] range
img = img.mean(2)[None, ...] # Make single color channel

transform = torchvision.transforms.Compose([
    xrv.datasets.XRayCenterCrop(),
    xrv.datasets.XRayResizer(224),
])

img = transform(img)
img = torch.from_numpy(img)

# Load model and process image
model = xrv.models.DenseNet(weights="densenet121-res224-all")
outputs = model(img[None,...]) # or model.features(img[None,...])
# Print results
results = dict(zip(model.pathologies, outputs[0].detach().numpy()))

print("=" * 60)
print("🩻 X-RAY ANALYSIS RESULTS")
print("=" * 60)
print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n📊 Raw Model Outputs:")
for pathology, score in results.items():
    print(f"  {pathology}: {score:.4f}")

# Send results to GPT-4 for medical interpretation
def analyze_with_gpt4(xray_results):
    """Send X-ray analysis results to GPT-4 for medical interpretation"""
    
    # Format the results for GPT-4
    results_text = "\n".join([f"- {pathology}: {score:.4f}" for pathology, score in xray_results.items()])
    
    prompt = f"""
You are an expert radiologist analyzing X-ray results from a deep learning model. The model has analyzed a chest X-ray and provided probability scores for various pathologies.

X-ray Analysis Results:
{results_text}

Please provide a comprehensive medical interpretation including:

1. **Primary Findings**: List the most significant findings (scores > 0.3 are typically considered positive)
2. **Clinical Significance**: Explain what these findings might indicate
3. **Recommended Actions**: Suggest appropriate follow-up care or additional testing
4. **Summary**: Provide a concise summary for the medical record

Important: This is for educational/research purposes. Always emphasize that final diagnosis requires clinical correlation and human radiologist review.

Format your response as a structured medical report.
"""

    try:
        # Initialize OpenAI client
        client = openai.OpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert radiologist providing medical interpretations of X-ray analysis results."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error connecting to GPT-4: {e}\n\nPlease ensure your OPENAI_API_KEY environment variable is set."

# Get GPT-4 analysis
print("\n🤖 SENDING TO GPT-4 FOR MEDICAL INTERPRETATION...")
print("-" * 60)

gpt4_analysis = analyze_with_gpt4(results)
print(gpt4_analysis)

print("\n" + "=" * 60)
print("⚠️  IMPORTANT DISCLAIMER")
print("=" * 60)
print("This analysis is for educational/research purposes only.")
print("Always consult with qualified medical professionals for actual diagnosis.")
print("AI analysis should supplement, not replace, clinical expertise.")
print("=" * 60)