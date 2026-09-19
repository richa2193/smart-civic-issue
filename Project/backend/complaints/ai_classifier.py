from PIL import Image
import os
import io

try:
    import torch
    from torchvision import models, transforms
    
    # Initialize model globally so it's only loaded once in memory
    weights = models.MobileNet_V2_Weights.DEFAULT
    model = models.mobilenet_v2(weights=weights)
    model.eval()
    
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    categories = weights.meta["categories"]
    MODEL_LOADED = True
except ImportError:
    print("AI dependencies (torch/torchvision) not installed. AI classification disabled.")
    MODEL_LOADED = False
except Exception as e:
    print(f"Error loading AI model: {e}")
    MODEL_LOADED = False

# Mapping from ImageNet labels (or substrings) to our civic categories
KEYWORD_MAPPING = {
    'Road Damage': ['pothole', 'street sign', 'traffic light', 'manhole cover', 'streetcar', 'plow', 'tractor', 'snowplow'],
    'Garbage': ['garbage truck', 'ashcan', 'trash can', 'garbage can', 'wastebin', 'carton', 'plastic bag', 'shopping cart', 'bucket', 'barrel'],
    'Tree Fallen': ['log', 'stump', 'tree', 'lumber'],
    'Water Leakage': ['fountain', 'water jug', 'fire engine', 'hose', 'plumbing'],
    'Street Light': ['pole', 'street lamp', 'spotlight', 'beacon'],
    'Traffic Signal': ['traffic light', 'street sign'],
}

def suggest_category_from_image(image_bytes):
    """
    Takes raw image bytes, runs it through MobileNetV2, 
    and returns a mapped category or None if low confidence/no match.
    """
    if not MODEL_LOADED:
        return None
        
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        input_tensor = preprocess(image)
        input_batch = input_tensor.unsqueeze(0) # create a mini-batch as expected by the model

        with torch.no_grad():
            output = model(input_batch)
            
        # Get top 3 predictions to increase chance of a good match
        probabilities = torch.nn.functional.softmax(output[0], dim=0)
        top3_prob, top3_catid = torch.topk(probabilities, 3)
        
        for i in range(top3_prob.size(0)):
            prob = top3_prob[i].item()
            category_name = categories[top3_catid[i]].lower()
            
            # If the confidence is at least 5% (since ImageNet is 1000 classes, 5% is somewhat relevant for generic objects)
            if prob > 0.05:
                # Check if this category name matches our keywords
                for civic_category, keywords in KEYWORD_MAPPING.items():
                    for keyword in keywords:
                        if keyword in category_name:
                            return civic_category
                            
        return None
    except Exception as e:
        print(f"Error in AI classification: {e}")
        return None
