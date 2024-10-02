import os
import json
import random
import argparse

def generate_json(directory_path, target_folder):
    files_list = []
    
    if not (target_folder in directory_path):
        return {}

    # Parcourir le répertoire pour récupérer les chemins des fichiers
    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            file_path = os.path.join(root, filename)

            # Vérifier si le chemin contient le dossier cible
            # if target_folder in file_path:
            # Extraire la partie du chemin à partir du dossier cible
            target_index = file_path.find(target_folder)
            relative_path = file_path[target_index:]
                
            # Générer le pourcentage aléatoire
            file_info = {
                "img": relative_path,  # Conserver le chemin relatif après "demo"
                "multiple": f"{random.uniform(0, 100):.0f}%"  # Générer un pourcentage aléatoire avec 2 décimales
            }
            files_list.append(file_info)
    
    # Convertir la liste en JSON
    json_output = json.dumps(files_list, indent=4)

    return json_output

# Exemple d'utilisation
#directory_path = "/chemin/vers/ton/repertoire"
#target_folder = "/demo"
#json_data = generate_json(directory_path, target_folder)
#print(json_data)


# if __name__ == "__main__":
#     # Utilisation d'argparse pour passer des arguments via le terminal
#     parser = argparse.ArgumentParser(description="Générer un JSON à partir de fichiers dans un répertoire")
#     parser.add_argument("directory", help="Le chemin du répertoire à analyser")
#     parser.add_argument("folder", help="Le dossier cible dans le chemin des fichiers (ex: /demo)")
    
#     args = parser.parse_args()
    
#     json_data = generate_json(args.directory, args.folder)
#     print(json_data)
# with open("output.json", "w") as json_file:
#     json.dump(files_list, json_file, indent=4)

if __name__ == "__main__":
    # Utilisation d'argparse pour passer des arguments via le terminal
    parser = argparse.ArgumentParser(description="Générer un JSON à partir de fichiers dans un répertoire")
    parser.add_argument("directory", help="Le chemin du répertoire à analyser")
    parser.add_argument("folder", help="Le dossier cible dans le chemin des fichiers (ex: /demo)")
    parser.add_argument("output_file", help="Le fichier où sauvegarder le JSON généré")

    args = parser.parse_args()
    
    # Générer le JSON
    json_data = generate_json(args.directory, args.folder)

    # Écrire le JSON dans un fichier
    with open(args.output_file, "w") as json_file:
        json_file.write(json_data)

    print(f"JSON sauvegardé dans {args.output_file}")

# exemple  d'utilisation
# python demo_get_vignettes.py /chemin/vers/ton/repertoire /demo output.json

# python3 src/demo_get_vignettes.py $HOME/Work/test/nextui/zooprocess_v10/public/demo/Zooscan_iado_wp2_2023_sn002/Zooscan_scan/_work/t_17_2_tot_1/vignettes/ /demo $HOME/Work/test/nextui/zooprocess_v10/public/demo/Zooscan_iado_wp2_2023_sn002/Zooscan_scan/_work/t_17_2_tot_1/vignettes.json

"""
{
 "src": "/Users/sebastiengalvagno/Work/test/nextui/zooprocess_v10/public/demo/Zooscan_iado_wp2_2023_sn002/Zooscan_scan/_work/t_17_2_tot_1/vignettes/",
 "base": "/demo",
 "output": "/Users/sebastiengalvagno/Work/test/nextui/zooprocess_v10/public/demo/Zooscan_iado_wp2_2023_sn002/Zooscan_scan/_work/t_17_2_tot_1/vignettes.json"
}
"""


"""
{
  "path": "/Users/sebastiengalvagno/Work/test/nextui/zooprocess_v10/public/demo/Zooscan_iado_wp2_2023_sn002/Zooscan_scan/_work/t_17_2_tot_1/vignettes/",
  "bearer": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY1OGRkN2VhMjRiYzEwYTRiZjFlMzdlMiIsImlhdCI6MTcyNzc3Mzc5MywiZXhwIjoxNzI4MDMyOTkzfQ.Nk6hjZ4in9rutRauXgffAW5wehkc9mZ3vyfO26Z-ThY"
}
"""