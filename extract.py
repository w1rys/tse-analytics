#%%
import argparse
import zipfile
import os
from rich.progress import track


DATA_DIR = "./data"
class ExtractFromZip:
    def __init__(self):
        pass

    def extract_zip(self, zip_file_path, extract_to):

        if not os.path.exists(zip_file_path):   
            raise FileNotFoundError(f"O arquivo {zip_file_path} não foi encontrado.")

        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

    def extract_ano(self, ano):

        folder = f"{DATA_DIR}/{ano}"

        files = [f for f in os.listdir(folder) if f.endswith('.zip')]

        for file in files:

            extract_to = os.path.join(folder, file.replace('.zip', ''))
            zip_file_path = os.path.join(folder, file)
            self.extract_zip(zip_file_path, extract_to)

        print(f"Arquivos extraídos do ano {ano} com sucesso!")
        
    def extract_anos(self, anos):
        for ano in track(anos, description="Extraindo arquivos..."):
            self.extract_ano(ano)
# %%
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Baixa arquivos do TSE para análise de dados eleitorais.")
    parser.add_argument("--inicio","-i", type=int, help="Ano inicial a ser baixado.")
    parser.add_argument("--fim", "-f", type=int, help="Ano final a ser baixado.")
    parser.add_argument("--intervalo", type=int, default= 2, help="Intervalo entre os anos a serem baixados.")
    args = parser.parse_args()

   

    extractor = ExtractFromZip()
    extractor.extract_anos(range(args.inicio, args.fim + 1, args.intervalo))

# %%