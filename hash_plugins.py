import hashlib
import glob
import os
from pathlib import Path

# On définit le chemin du fichier de stockage
PLUGIN_DIR = "minima/plugins"
HASH_FILE = os.path.join(PLUGIN_DIR, "trusted_hashes.txt")

print(f"--- Mise à jour du registre de sécurité ---")

lines_to_write = []

# On scanne tous les fichiers .py du dossier plugins
for f_path in glob.glob(os.path.join(PLUGIN_DIR, "*.py")):
    filename = os.path.basename(f_path)
    
    # On ignore les fichiers internes pour ne pas s'auto-signer
    if filename in ["__init__.py", "plugin_validator.py", "hash_plugins.py"]:
        continue
        
    try:
        with open(f_path, "rb") as f:
            # Calcul du SHA256
            h = hashlib.sha256(f.read()).hexdigest()
            
            # On prépare la ligne au format : HASH CHEMIN
            # On utilise os.path.join pour que le chemin soit propre (Windows/Linux)
            entry = f"{h} {PLUGIN_DIR}/{filename}\n"
            lines_to_write.append(entry)
            print(f"✅ Signé : {filename}")
            
    except Exception as e:
        print(f"❌ Erreur sur {filename} : {e}")

# Écriture physique dans le fichier
with open(HASH_FILE, "w", encoding="utf-8") as f_out:
    f_out.writelines(lines_to_write)

print(f"\n🚀 Terminé ! {len(lines_to_write)} plugins ont été enregistrés dans {HASH_FILE}")