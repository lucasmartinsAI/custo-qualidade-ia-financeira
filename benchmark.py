"""Benchmark v3: roda varios casos de duration de Macaulay em cada modelo local (Ollama)
e grava as metricas em results/resultados_casos.csv.

Mudancas da v3 (depois que o 3B travou no caso 14 e derrubou a rodada da noite):
- limita o tamanho de cada resposta (NUM_PREDICT), para o modelo nao entrar em loop
- se um caso falhar (timeout, erro de conexao), registra a falha e segue para o proximo
- nova coluna 'obs' no CSV: marca 'truncado' ou 'FALHA: ...'
- o CSV antigo (sem a coluna 'obs') e atualizado sozinho, com backup

Uso:
    python benchmark.py

Se for interrompido (Ctrl+C), basta rodar de novo: ele pula o que ja foi feito.
"""

import csv
import os
import random
import re
import shutil
import statistics
from datetime import datetime

import requests

URL = "http://localhost:11434/api/generate"
MODELOS = ["qwen2.5:3b", "qwen2.5"]  # edite aqui para incluir outros modelos
N_CASOS = 30
SEED_CASOS = 7        # fixa quais casos sao sorteados (resultado reproduzivel)
LIMITE_ACERTO = 1.0   # erro maximo (em %) para contar como acerto
NUM_PREDICT = 4000    # maximo de tokens por resposta (a maior ate agora foi 3410)
TIMEOUT_S = 1800      # espera maxima por caso (30 min)
PASTA = "results"
ARQUIVO = os.path.join(PASTA, "resultados_casos.csv")

COLUNAS = [
    "data", "caso", "cupom_pct", "anos", "taxa_pct", "modelo", "resposta",
    "gabarito", "erro_pct", "tempo_total_s", "tokens_gerados", "tokens_por_s",
    "metodo_certo", "obs",
]

PROMPT = (
    "Título prefixado: valor de face R$ 1.000, cupom de {cupom}% ao ano pago anualmente, "
    "vencimento em {anos} anos, taxa de desconto de {taxa}% ao ano. Calcule a duration de "
    "Macaulay, em anos. Mostre a tabela de fluxos descontados e termine com uma linha "
    "no formato: RESPOSTA: X anos"
)


def gabarito(cupom_pct, anos, taxa_pct, face=1000.0):
    """Duration de Macaulay exata (cupom anual, face R$ 1.000)."""
    cupom, taxa = cupom_pct / 100, taxa_pct / 100
    fluxos = [face * cupom] * (anos - 1) + [face * (1 + cupom)]
    vp = [c / (1 + taxa) ** (t + 1) for t, c in enumerate(fluxos)]
    return sum((t + 1) * v for t, v in enumerate(vp)) / sum(vp)


def gerar_casos(n):
    """O caso 1 e o do primeiro experimento; os demais sao sorteados com seed fixa."""
    rng = random.Random(SEED_CASOS)
    casos = [(10, 5, 5)]  # (cupom %, anos, taxa %)
    while len(casos) < n:
        c = (rng.randint(6, 14), rng.randint(3, 10), rng.randint(4, 16))
        if c not in casos:
            casos.append(c)
    return casos[:n]


def extrai_resposta(texto):
    """Pega o numero da ultima linha 'RESPOSTA: X anos'. Retorna None se nao achar."""
    achados = re.findall(r"RESPOSTA:\s*\**\s*(\d+(?:[.,]\d+)?)", texto)
    if not achados:
        return None
    return float(achados[-1].replace(",", "."))


def roda(modelo, prompt):
    corpo = {
        "model": modelo,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0, "seed": 42, "num_predict": NUM_PREDICT},
    }
    r = requests.post(URL, json=corpo, timeout=TIMEOUT_S)
    r.raise_for_status()
    return r.json()


def garante_coluna_obs():
    """Se o CSV e da versao antiga (sem 'obs'), guarda um backup e reescreve com a coluna."""
    if not os.path.exists(ARQUIVO):
        return
    with open(ARQUIVO, newline="", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        if "obs" in (leitor.fieldnames or []):
            return
        linhas = list(leitor)
    shutil.copyfile(ARQUIVO, ARQUIVO.replace(".csv", "_backup.csv"))
    with open(ARQUIVO, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS)
        w.writeheader()
        for linha in linhas:
            linha["obs"] = ""
            w.writerow(linha)
    print(f"CSV antigo atualizado com a coluna 'obs' ({len(linhas)} linhas). Backup salvo.")


def ja_feitos():
    """Pares (modelo, caso) que ja estao no CSV (inclusive os que falharam), para retomar."""
    if not os.path.exists(ARQUIVO):
        return set()
    with open(ARQUIVO, encoding="utf-8") as f:
        return {(l["modelo"], int(l["caso"])) for l in csv.DictReader(f)}


def resumo():
    with open(ARQUIVO, encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    print("\n=== RESUMO ===")
    for modelo in MODELOS:
        L = [l for l in linhas if l["modelo"] == modelo]
        if not L:
            continue
        erros = [float(l["erro_pct"]) for l in L if l["erro_pct"] != ""]
        acertos = sum(1 for e in erros if e <= LIMITE_ACERTO)
        truncados = sum(1 for l in L if l["obs"] == "truncado")
        falhas = sum(1 for l in L if l["obs"].startswith("FALHA"))
        medidos = [l for l in L if l["tokens_por_s"] != ""]
        print(f"{modelo}: {len(L)} casos | acertos (erro <= {LIMITE_ACERTO}%): {acertos}/{len(L)}")
        print(f"   sem resposta: {len(L) - len(erros)} (truncados: {truncados}, falhas: {falhas})")
        if erros:
            print(f"   erro medio {statistics.mean(erros):.2f}% | erro mediano {statistics.median(erros):.2f}%")
        if medidos:
            tempo = statistics.mean(float(l["tempo_total_s"]) for l in medidos)
            tps = statistics.mean(float(l["tokens_por_s"]) for l in medidos)
            print(f"   tempo medio {tempo:.0f}s | velocidade media {tps:.1f} tok/s")


def main():
    os.makedirs(PASTA, exist_ok=True)
    garante_coluna_obs()
    casos = gerar_casos(N_CASOS)
    feitos = ja_feitos()
    novo = not os.path.exists(ARQUIVO)

    with open(ARQUIVO, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS)
        if novo:
            w.writeheader()

        for modelo in MODELOS:
            for k, (cupom, anos, taxa) in enumerate(casos, 1):
                if (modelo, k) in feitos:
                    continue
                alvo = gabarito(cupom, anos, taxa)
                print(f"[{modelo}] caso {k}/{len(casos)}: cupom {cupom}%, {anos} anos, "
                      f"taxa {taxa}% (gabarito {alvo:.3f})...")

                base = {
                    "data": datetime.now().isoformat(timespec="seconds"),
                    "caso": k, "cupom_pct": cupom, "anos": anos, "taxa_pct": taxa,
                    "modelo": modelo, "gabarito": round(alvo, 4), "metodo_certo": "",
                }

                try:
                    d = roda(modelo, PROMPT.format(cupom=cupom, anos=anos, taxa=taxa))
                except requests.exceptions.RequestException as e:
                    print(f"   FALHA ({type(e).__name__}). Registrando e seguindo para o proximo.")
                    w.writerow({**base, "resposta": "", "erro_pct": "", "tempo_total_s": "",
                                "tokens_gerados": "", "tokens_por_s": "",
                                "obs": f"FALHA: {type(e).__name__}"})
                    f.flush()
                    continue

                texto = d.get("response", "")
                nome = modelo.replace(":", "_")
                with open(os.path.join(PASTA, f"{nome}_caso{k}.txt"), "w", encoding="utf-8") as t:
                    t.write(texto)

                resposta = extrai_resposta(texto)
                erro = None if resposta is None else round(abs(resposta - alvo) / alvo * 100, 2)
                tempo = d["total_duration"] / 1e9
                tps = d["eval_count"] / (d["eval_duration"] / 1e9)
                obs = "truncado" if d.get("done_reason") == "length" else ""

                w.writerow({**base, "resposta": resposta, "erro_pct": erro,
                            "tempo_total_s": round(tempo, 1), "tokens_gerados": d["eval_count"],
                            "tokens_por_s": round(tps, 2), "obs": obs})
                f.flush()
                print(f"   resposta={resposta}  erro={erro}%  tempo={tempo:.0f}s  "
                      f"{tps:.1f} tok/s  {obs}")

    resumo()
    print(f"\nPronto. Resultados em {ARQUIVO}")


if __name__ == "__main__":
    main()
