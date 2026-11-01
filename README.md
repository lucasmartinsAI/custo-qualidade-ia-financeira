# Custo × Qualidade em IA financeira

Quanto custa, e quanto de qualidade se perde, ao trocar um modelo de API de topo por um modelo mais barato ou por um modelo open rodando localmente em tarefas de renda fixa?

## Primeiro experimento (01/11/2026)

Tarefa: calcular a duration de Macaulay de um título prefixado
(face R$ 1.000, cupom 10% a.a., 5 anos, desconto 5% a.a.). Gabarito: 4,25 anos.
Máquina: CPU apenas (Intel Iris Xe, 24 GB RAM), via Ollama.
Parâmetros: temperatura 0, seed 42.

| Modelo | Resposta | Erro | Tempo | Velocidade | Método certo? |
|---|---|---|---|---|---|
| qwen2.5:3b | 5,13 anos | 20,6% | 2m29 | 10,7 tok/s | Não |
| qwen2.5 (7B) | a medir | | | | |

Observação: o 3B conhece a fórmula, mas monta fluxos de caixa errados.

## Roadmap
- [ ] Gabarito com 30-50 documentos financeiros
- [ ] Comparação com API de topo e API barata
- [ ] Roteador entre modelos e economia medida
- [ ] Servidor MCP expondo o benchmark
