#!/usr/bin/env python3
"""
Enhanced X-ray Analysis with GPT-4 Integration
Analyzes chest X-rays using torchxrayvision and gets medical interpretation from GPT-4
"""

import torchxrayvision as xrv
import skimage, torch, torchvision
import openai
import json
import os
import argparse
from datetime import datetime
from pathlib import Path
import dotenv
# Load environment variables from .env file
dotenv.load_dotenv(dotenv_path=".env.openai")

def load_and_preprocess_image(image_path):
    """Load and preprocess X-ray image for analysis"""
    print(f"📂 Loading image: {image_path}")
    
    # Prepare the image
    img = skimage.io.imread(image_path)
    img = xrv.datasets.normalize(img, 255)  # convert 8-bit image to [-1024, 1024] range
    img = img.mean(2)[None, ...]  # Make single color channel

    transform = torchvision.transforms.Compose([
        xrv.datasets.XRayCenterCrop(),
        xrv.datasets.XRayResizer(224),
    ])

    img = transform(img)
    img = torch.from_numpy(img)
    
    return img

def analyze_xray_with_model(img):
    """Analyze X-ray image using torchxrayvision model"""
    print("🔬 Loading DenseNet model and analyzing...")
    
    # Load model and process image
    model = xrv.models.DenseNet(weights="densenet121-res224-all")
    outputs = model(img[None,...])
    
    # Get results
    results = dict(zip(model.pathologies, outputs[0].detach().numpy()))
    
    return results

def analyze_with_gpt4(xray_results, patient_info=None):
    """Send X-ray analysis results to GPT-4 for medical interpretation"""
    
    # Format the results for GPT-4
    results_text = "\n".join([f"- {pathology}: {score:.4f}" for pathology, score in xray_results.items()])
    
    # Add patient context if provided
    patient_context = ""
    if patient_info:
        patient_context = f"\nPatient Information:\n{patient_info}\n"
    
    prompt = f"""
You are an expert radiologist analyzing X-ray results from a deep learning model. The model has analyzed a chest X-ray and provided probability scores for various pathologies.

{patient_context}
X-ray Analysis Results:
{results_text}

Please provide a comprehensive medical interpretation including:

1. **Primary Findings**: List the most significant findings (scores > 0.3 are typically considered positive)
2. **Clinical Significance**: Explain what these findings might indicate
3. **Differential Diagnosis**: List possible conditions based on the findings
4. **Recommended Actions**: Suggest appropriate follow-up care or additional testing
5. **Clinical Summary**: Provide a concise summary suitable for medical records

Important Guidelines:
- Scores > 0.5 are considered highly suggestive
- Scores 0.3-0.5 are moderately suggestive
- Scores < 0.3 are typically not clinically significant
- Always emphasize need for clinical correlation

Format your response as a structured medical report with clear sections.
"""

    try:
        # Check for API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return "❌ Error: OPENAI_API_KEY environment variable not set.\n\nPlease set your OpenAI API key:\nexport OPENAI_API_KEY='your-api-key-here'"
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        print("🤖 Sending to GPT-4 for medical interpretation...")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert radiologist providing medical interpretations of X-ray analysis results. Provide structured, professional medical reports."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ Error connecting to GPT-4: {e}"

def save_report(image_path, raw_results, gpt4_analysis, output_file=None):
    """Save the complete analysis report to a file"""
    
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_name = Path(image_path).stem
        output_file = f"xray_analysis_{image_name}_{timestamp}.txt"
    
    report_content = f"""
CHEST X-RAY ANALYSIS REPORT
={'=' * 50}

Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Image File: {image_path}

RAW MODEL RESULTS
{'-' * 30}
"""
    
    for pathology, score in raw_results.items():
        report_content += f"{pathology}: {score:.4f}\n"
    
    report_content += f"""
GPT-4 MEDICAL INTERPRETATION
{'-' * 30}
{gpt4_analysis}

DISCLAIMER
{'-' * 30}
This analysis is for educational/research purposes only.
Always consult with qualified medical professionals for actual diagnosis.
AI analysis should supplement, not replace, clinical expertise.
"""
    
    with open(output_file, 'w') as f:
        f.write(report_content)
    
    print(f"📄 Report saved to: {output_file}")
    return output_file

def main():
    image_path = "xray-images/xray1.jpg"
    try:
        # Load and preprocess image
        img = load_and_preprocess_image(image_path)
        
        # Analyze with torchxrayvision model
        results = analyze_xray_with_model(img)
        
        # Display raw results
        print(f"\n📊 Raw Model Results:")
        print("-" * 30)
        for pathology, score in results.items():
            indicator = "🔴" if score > 0.5 else "🟡" if score > 0.3 else "🟢"
            print(f"  {indicator} {pathology}: {score:.4f}")
        
        # Get GPT-4 analysis unless skipped
        gpt4_analysis = ""
        if not args.no_gpt4:
            print(f"\n🤖 GPT-4 Medical Interpretation:")
            print("-" * 60)
            gpt4_analysis = analyze_with_gpt4(results, args.patient_info)
            print(gpt4_analysis)
        
        # Save report
        report_file = save_report(args.image_path, results, gpt4_analysis, args.output)
        
        print(f"\n✅ Analysis complete!")
        if not args.no_gpt4:
            print("💡 Tip: Use this analysis to create clinical notes in the EMR system")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")

if __name__ == "__main__":
    main()
