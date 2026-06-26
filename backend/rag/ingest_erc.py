import os
import sys

# Bootstrap d'import : ajoute la racine du repo pour importer backend.config
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Navigate to project root
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from backend.config.settings import require_mistral_api_key, VECTOR_DB_DIR
except ImportError:
    print(f"❌ ERREUR: Impossible d'importer backend.config.settings depuis {project_root}")
    sys.exit(1)

from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_mistralai import MistralAIEmbeddings
from langchain_chroma import Chroma

def index_erc_folder(repo_path):
    """
    Indexe les ERCs dans une collection isolée.
    """
    
    if not os.path.exists(repo_path):
        print(f"❌ Erreur : Le dossier source n'existe pas : {repo_path}")
        return

    # Découpage intelligent (Markdown Header Splitter)
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

    print("🔑 Initialisation de Mistral Embeddings...")
    embeddings = MistralAIEmbeddings(mistral_api_key=require_mistral_api_key())
    
    # ⚠️ IMPORTANT : On utilise la collection spécifique "erc_standards"
    print(f"🗄️  Connexion à la DB : {VECTOR_DB_DIR}")
    
    try:
        vector_db = Chroma(
            persist_directory=str(VECTOR_DB_DIR),
            embedding_function=embeddings,
            collection_name="erc_standards"  # <--- SEPARATION
        )
    except Exception as e:
        print(f"❌ Erreur ChromaDB: {e}")
        return

    print(f"🚀 Indexation depuis : {repo_path}")
    count = 0

    for filename in os.listdir(repo_path):
        if filename.endswith(".md"):
            file_path = os.path.join(repo_path, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                splits = header_splitter.split_text(content)
                
                erc_id = filename.lower().replace("erc-", "").replace("erc", "").replace(".md", "")
                
                for split in splits:
                    split.metadata["erc_number"] = erc_id
                    split.metadata["source"] = "ethereum_ercs"
                    split.metadata["filename"] = filename

                vector_db.add_documents(splits)
                print(f"✅ Indexé : {filename} ({len(splits)} chunks)")
                count += 1
                
            except Exception as e:
                print(f"⚠️ Erreur fichier {filename} : {e}")

    print(f"✨ Terminé ! {count} fichiers traités.")

if __name__ == "__main__":
    # Tolère les variantes de casse (ERCs/ERCS) pour compatibilité multi-OS.
    data_root = os.path.join(project_root, "data")
    candidates = [
        os.path.join(data_root, "ERCs"),
        os.path.join(data_root, "ERCS"),
    ]
    path_to_data = next((p for p in candidates if os.path.isdir(p)), candidates[0])
    
    print(f"🎯 Dossier Data cible : {path_to_data}")
    index_erc_folder(path_to_data)
