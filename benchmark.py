"""Benchmark de custo x qualidade: roda o prompt padrao em modelos locais (Ollama)
e grava as metricas em results/resultados.csv.

Uso:
    python benchmark.py
"""

import csv
import os
import re
from datetime import datetime

import requests

URL = "http://localhost:11434/api/generate"
MODELOS = ["qwen2.5:3b", "qwen2.5"]  # edite aqui para incluir outros modelos
REPETICOES = 1
PASTA = "results"

PROMPT = (
    "Título prefixado: valor de face R$ 1.000, cupom de 10% ao ano pago anualmente, "
    "vencimento em 5 anos, taxa de desconto de 5% ao ano. Calcule a duration de "
    "Macaulay, em anos. Mostre a tabela de fluxos descontados e termine com uma linha "
    "no formato: RESPOSTA: X anos"
)


def gabarito(face=1000.0, cupom=0.10, anos=5, taxa=0.05):
    """Duration de Macaulay calculada de forma exata (cupom anual)."""
    fluxos = [face * cupom] * (anos - 1) + [face * (1 + cupom)]
    vp = [c / (1 + taxa) ** (t + 1) for t, c in enumerate(fluxos)]
    return sum((t + 1) * v for t, v in enumerate(vp)) / sum(vp)


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
        "options": {"temperature": 0, "seed": 42},
    }
    r = requests.post(URL, json=corpo, timeout=1800)
    r.raise_for_status()
    return r.json()


def main():
    os.makedirs(PASTA, exist_ok=True)
    alvo = gabarito()
    print(f"Gabarito: {alvo:.4f} anos")

    caminho = os.path.join(PASTA, "resultados.csv")
    novo = not os.path.exists(caminho)
    colunas = [
        "data", "modelo", "rodada", "resposta", "gabarito", "erro_pct",
        "tempo_total_s", "tokens_gerados", "tokens_por_s", "metodo_certo",
    ]

    with open(caminho, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas)
        if novo:
            w.writeheader()

        for modelo in MODELOS:
            for i in range(1, REPETICOES + 1):
                print(f"Rodando {modelo} (rodada {i})...")
                d = roda(modelo, PROMPT)

                texto = d.get("response", "")
                nome = modelo.replace(":", "_")
                with open(os.path.join(PASTA, f"{nome}_rodada{i}.txt"), "w", encoding="utf-8") as t:
                    t.write(texto)

                resposta = extrai_resposta(texto)
                erro = None if resposta is None else round(abs(resposta - alvo) / alvo * 100, 2)
                tempo = d["total_duration"] / 1e9
                tps = d["eval_count"] / (d["eval_duration"] / 1e9)

                w.writerow({
                    "data": datetime.now().isoformat(timespec="seconds"),
                    "modelo": modelo,
                    "rodada": i,
                    "resposta": resposta,
                    "gabarito": round(alvo, 4),
                    "erro_pct": erro,
                    "tempo_total_s": round(tempo, 1),
                    "tokens_gerados": d["eval_count"],
                    "tokens_por_s": round(tps, 2),
                    "metodo_certo": "",  # preencher a mao depois de ler o .txt
                })
                f.flush()
                print(f"  resposta={resposta}  erro={erro}%  tempo={tempo:.0f}s  {tps:.1f} tok/s")

    print(f"Pronto. Resultados em {caminho}")


if __name__ == "__main__":
    main()
