from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import torch
import time

def main():
    print("Loading Clinical BERT model (this might take a few minutes for the first download)...")
    start_time = time.time()
    
    # Using a lightweight but highly capable medical model for embeddings
    model_name = 'pritamdeka/S-PubMedBert-MS-MARCO'
    
    try:
        model = SentenceTransformer(model_name)
    except Exception as e:
        print(f"Failed to load specific medical model due to: {e}")
        print("Falling back to all-MiniLM-L6-v2...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
    print(f"Model loaded in {time.time() - start_time:.2f} seconds.")
    print("Device used:", model.device)
    
    # Let's run a quick semantic test
    print("\n--- Running Semantic Test ---")
    lab_text = "Stool culture for Vibrio cholerae"
    tmlt_texts = [
        "Vibrio cholerae culture", 
        "Urine examination",
        "Complete Blood Count",
        "Stool examination for parasites"
    ]
    
    # Generate embeddings
    lab_emb = model.encode([lab_text])
    tmlt_embs = model.encode(tmlt_texts)
    
    # Calculate cosine similarity
    similarities = cosine_similarity(lab_emb, tmlt_embs)[0]
    
    print(f"Input Lab: '{lab_text}'\n")
    for i, tmlt in enumerate(tmlt_texts):
        print(f"Compared with TMLT: '{tmlt}' -> Similarity Score: {similarities[i]:.4f}")
        
    print("\nStep 2 Completed successfully! Model is ready for the mapping pipeline.")

if __name__ == "__main__":
    main()
