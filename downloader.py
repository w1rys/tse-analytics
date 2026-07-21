# %%
from pathlib import Path
import argparse
import time
import http
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TextColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
)

class DownloadTSE:
    def __init__(self, pasta_destino: str = "data"):
        self.pasta_destino = Path(pasta_destino)
        self.pasta_destino.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()

        retry = Retry(
            total=5,
            connect=5,
            read=5,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )

        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=10,
            pool_maxsize=10,
        )

        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
            )
        }

    def _download(
        self,
        url: str,
        nome_arquivo: str,
        ano: int,
        tentativas: int = 5,
        chunk_size: int = 1024 * 1024,
    ) -> bool:
        pasta_ano = self.pasta_destino / str(ano)
        pasta_ano.mkdir(parents=True, exist_ok=True)

        caminho_final = pasta_ano / nome_arquivo
        caminho_parcial = pasta_ano / f"{nome_arquivo}.part"

        # Ignora o arquivo caso ele já tenha sido baixado
        if caminho_final.exists() and caminho_final.stat().st_size > 0:
            print(f"↷ {nome_arquivo} já existe. Download ignorado.")
            return True

        for tentativa in range(1, tentativas + 1):
            try:
                tamanho_existente = (
                    caminho_parcial.stat().st_size
                    if caminho_parcial.exists()
                    else 0
                )

                headers = self.headers.copy()

                # Continua um download que foi interrompido
                if tamanho_existente > 0:
                    headers["Range"] = f"bytes={tamanho_existente}-"

                with self.session.get(
                    url,
                    headers=headers,
                    stream=True,
                    timeout=(30, 300),
                ) as response:

                    if response.status_code == 404:
                        print(
                            f"✗ Erro ao baixar {nome_arquivo}. "
                            f"Status Code: 404"
                        )

                        caminho_parcial.unlink(missing_ok=True)
                        return False

                    if response.status_code not in (http.HTTPStatus.OK, 206):
                        print(
                            f"✗ Erro ao baixar {nome_arquivo}. "
                            f"Status Code: {response.status_code}"
                        )
                        return False

                    # O servidor não permitiu continuar o download
                    if tamanho_existente > 0 and response.status_code == http.HTTPStatus.OK:
                        tamanho_existente = 0
                        caminho_parcial.unlink(missing_ok=True)

                    tamanho_resposta = int(
                        response.headers.get("content-length", 0)
                    )

                    tamanho_total = tamanho_existente + tamanho_resposta

                    modo = "ab" if tamanho_existente > 0 else "wb"

                    with Progress(
                        TextColumn("[bold blue]{task.description}"),
                        BarColumn(),
                        DownloadColumn(),
                        TransferSpeedColumn(),
                        TimeRemainingColumn(),
                    ) as progress:

                        tarefa = progress.add_task(
                            nome_arquivo,
                            total=tamanho_total or None,
                            completed=tamanho_existente,
                        )

                        with open(caminho_parcial, modo) as arquivo:
                            for bloco in response.iter_content(
                                chunk_size=chunk_size
                            ):
                                if not bloco:
                                    continue

                                arquivo.write(bloco)

                                progress.update(
                                    tarefa,
                                    advance=len(bloco),
                                )

                tamanho_baixado = caminho_parcial.stat().st_size

                if tamanho_total and tamanho_baixado < tamanho_total:
                    raise IOError(
                        f"Download incompleto: "
                        f"{tamanho_baixado} de "
                        f"{tamanho_total} bytes."
                    )

                caminho_parcial.replace(caminho_final)

                tamanho_mb = (
                    caminho_final.stat().st_size
                    / (1024 * 1024)
                )

                print(
                    f"✓ {nome_arquivo} baixado com sucesso "
                    f"({tamanho_mb:.2f} MB)."
                )

                return True

            except (
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout,
                requests.exceptions.Timeout,
                IOError,
            ) as erro:
                print(
                    f"\n⚠ Conexão interrompida em {nome_arquivo}. "
                    f"Tentativa {tentativa}/{tentativas}."
                )

                print(f"Motivo: {erro}")

                if tentativa < tentativas:
                    espera = tentativa * 5

                    print(
                        f"Retomando o download em "
                        f"{espera} segundos..."
                    )

                    time.sleep(espera)

                else:
                    print(
                        f"✗ Não foi possível concluir "
                        f"{nome_arquivo} após "
                        f"{tentativas} tentativas."
                    )

                    return False

            except requests.exceptions.RequestException as erro:
                print(
                    f"✗ Erro de requisição em "
                    f"{nome_arquivo}: {erro}"
                )
                return False

            except OSError as erro:
                print(
                    f"✗ Erro ao salvar "
                    f"{nome_arquivo}: {erro}"
                )
                return False

        return False

    def download_consulta_candidatura(self, ano: int) -> bool:
        nome = f"consulta_cand_{ano}.zip"

        url = (
            "https://cdn.tse.jus.br/estatistica/sead/odsele/"
            f"consulta_cand/{nome}"
        )

        return self._download(
            url,
            nome,
            ano,
        )

    def download_bens_candidatos(self, ano: int) -> bool:
        nome = f"bem_candidato_{ano}.zip"

        url = (
            "https://cdn.tse.jus.br/estatistica/sead/odsele/"
            f"bem_candidato/{nome}"
        )

        return self._download(
            url,
            nome,
            ano,
        )

    def download_coligacoes(self, ano: int) -> bool:
        nome = f"consulta_coligacao_{ano}.zip"

        url = (
            "https://cdn.tse.jus.br/estatistica/sead/odsele/"
            f"consulta_coligacao/{nome}"
        )

        return self._download(
            url,
            nome,
            ano,
        )

    def download_motivo_cassacao(self, ano: int) -> bool:
        nome = f"motivo_cassacao_{ano}.zip"

        url = (
            "https://cdn.tse.jus.br/estatistica/sead/odsele/"
            f"motivo_cassacao/{nome}"
        )

        return self._download(
            url,
            nome,
            ano,
        )

    def download_votacao_candidato_munzona(
        self,
        ano: int,
    ) -> bool:
        nome = f"votacao_candidato_munzona_{ano}.zip"

        url = (
            "https://cdn.tse.jus.br/estatistica/sead/odsele/"
            f"votacao_candidato_munzona/{nome}"
        )

        return self._download(
            url,
            nome,
            ano,
        )

    def download_ano(self, ano: int) -> dict[str, bool]:
        print(
            f"\n{'=' * 15} "
            f"Baixando arquivos do TSE - {ano} "
            f"{'=' * 15}\n"
        )

        resultados = {
            "consulta_cand":
                self.download_consulta_candidatura(ano),

            "bem_candidato":
                self.download_bens_candidatos(ano),

            "consulta_coligacao":
                self.download_coligacoes(ano),

            "motivo_cassacao":
                self.download_motivo_cassacao(ano),

            "votacao_candidato_munzona":
                self.download_votacao_candidato_munzona(ano),
        }

        return resultados

    def download_anos(self, anos) -> None:
        resumo = {}

        for ano in anos:
            try:
                resumo[ano] = self.download_ano(ano)

            except KeyboardInterrupt:
                print("\n\nDownload interrompido pelo usuário.")

                print(
                    "Os arquivos parciais foram mantidos e "
                    "poderão ser retomados na próxima execução."
                )

                break

            except Exception as erro:
                print(
                    f"\n✗ Erro inesperado no ano {ano}: {erro}"
                )

                print(
                    "O programa continuará para o próximo ano."
                )

                resumo[ano] = {
                    "erro_inesperado": False
                }

        self._mostrar_resumo(resumo)

    @staticmethod
    def _mostrar_resumo(resumo: dict) -> None:
        print("\n" + "=" * 60)
        print("RESUMO DOS DOWNLOADS")
        print("=" * 60)

        for ano, arquivos in resumo.items():
            concluidos = sum(
                resultado is True
                for resultado in arquivos.values()
            )

            total = len(arquivos)

            print(
                f"{ano}: "
                f"{concluidos}/{total} "
                f"arquivos concluídos"
            )

# %%
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Baixa arquivos do TSE para análise de dados eleitorais.")
    parser.add_argument("--inicio","-i", type=int, help="Ano inicial a ser baixado.")
    parser.add_argument("--fim", "-f", type=int, help="Ano final a ser baixado.")
    parser.add_argument("--intervalo", type=int, default= 2, help="Intervalo entre os anos a serem baixados.")
    args = parser.parse_args()

    downloader = DownloadTSE(pasta_destino="data")
    downloader.download_anos(range(args.inicio, args.fim + 1, args.intervalo))
# %%
