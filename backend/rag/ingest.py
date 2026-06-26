import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

from langchain_core.documents import Document 
from langchain_chroma import Chroma
from langchain_mistralai import MistralAIEmbeddings
# On réintègre le splitter indispensable
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Bootstrap d'import : ajoute la racine du repo pour importer backend.config
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # Navigate to project root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.settings import DATA_DIR, VECTOR_DB_DIR, require_mistral_api_key

load_dotenv()

# Chemins (alignés sur la config du projet)
RAG_DATA_DIR = DATA_DIR / "data_rag"
CONTRACTS_DIR = RAG_DATA_DIR / "contracts"
TESTS_DIR = RAG_DATA_DIR / "tests"
METADATA_FILE = RAG_DATA_DIR / "metadata.json"
GENERATOR_COLLECTION = "langchain"

def load_metadata():
    if not METADATA_FILE.exists():
        return []
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_text_files(folder):
    docs = []
    if not folder.exists():
        print(f"⚠️ Warning: Folder not found {folder}")
        return docs
        
    for filename in os.listdir(folder):
        if filename.endswith((".txt", ".sol", ".js")):
            path = os.path.join(folder, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                docs.append((filename, content))
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    return docs

def associate_metadata(docs, metadata):
    docs_with_meta = []
    for fname, content in docs:
        meta = next((m for m in metadata if m.get("filename") == fname), {})
        metadata_flat = {k: str(v) for k, v in meta.items()}
        
        if "source" not in metadata_flat:
            metadata_flat["source"] = fname
            
        docs_with_meta.append(Document(page_content=content, metadata=metadata_flat))
    return docs_with_meta

def main():
    print("🔄 Chargement des données...")
    metadata = load_metadata()
    
    # 1. Chargement
    contracts_docs = load_text_files(CONTRACTS_DIR)
    tests_docs = load_text_files(TESTS_DIR)
    all_docs = contracts_docs + tests_docs
    
    if not all_docs:
        print("❌ Aucun document trouvé !")
        return

    print("🔗 Association des métadonnées...")
    full_docs = associate_metadata(all_docs, metadata)

    # 2. DÉCOUPAGE (La correction est ici)
    # On découpe les fichiers trop gros en morceaux de 1500 caractères environ
    print(f"✂️ Découpage des {len(full_docs)} fichiers en chunks digestes pour l'API...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        separators=["contract ", "describe(", "function ", "interface ", "\n\n", "\n"]
    )
    
    # split_documents conserve les métadonnées pour chaque morceau !
    splitted_docs = text_splitter.split_documents(full_docs)
    
    print(f"   -> Résultat : {len(splitted_docs)} morceaux à indexer.")

    # 3. Indexation
    api_key = require_mistral_api_key()

    embeddings = MistralAIEmbeddings(mistral_api_key=api_key)
    persist_dir = str(VECTOR_DB_DIR)
    
    print(f"💾 Envoi vers Mistral et sauvegarde dans {persist_dir}...")
    
    # Chroma gère automatiquement les batches (par lots)
    vectordb = Chroma.from_documents(
        documents=splitted_docs, # On envoie les morceaux découpés, pas les fichiers entiers
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_name=GENERATOR_COLLECTION,
    )

    print(f"✅ [SUCCESS] Base de données créée avec succès !")

if __name__ == "__main__":
    main()
