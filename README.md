# Custo × Qualidade em IA financeira

Quanto custa, e quanto de qualidade se perde, ao trocar um modelo de API de topo por um modelo mais barato ou por um modelo open rodando localmente em tarefas de renda fixa?

Projeto em andamento. Este repositório registra o benchmark passo a passo.

## Experimento 1: duration de Macaulay (10 casos, modelos open locais)

**Tarefa:** calcular a duration de Macaulay de um título prefixado (face R$ 1.000, cupom anual). Os casos variam cupom (6-14%), prazo (3-10 anos) e taxa de desconto (4-16%), sorteados com seed fixa. O gabarito é calculado por código.

**Ambiente:** Windows, só CPU (Intel Iris Xe integrada, 24 GB de RAM), modelos via [Ollama](https://ollama.com). Temperatura 0, seed 42, mesmo prompt para todos.

| Métrica | qwen2.5 3B | qwen2.5 7B |
|---|---|---|
| Acertos (erro ≤ 1%) | 0/10 | 4/10 |
| Acertos (erro ≤ 5%) | 0/10 | 6/10 |
| Erro mediano | 48,6% | 2,4% |
| Erro médio | 57,1% | 23,3% |
| Respostas impossíveis* | 4/10 | 0/10 |
| Sem resposta no formato | 1 | 0 |
| Tempo médio por caso | 206 s | 396 s |
| Velocidade média | 7,7 tok/s | 3,4 tok/s |

\* A duration de Macaulay de um título com cupom anual está sempre entre 1 e o prazo. Resposta fora disso é impossível.

### O que os dados mostram

- **3B** não serve para essa tarefa: nenhum acerto, e em 4 dos 10 casos deu uma resposta matematicamente impossível.
- **7B** é "tudo ou nada": 6 casos com erro de até 3% e 4 com erros de 15% a 80%, sem meio-termo. Por isso média e mediana diferem tanto.
- **Qualidade custou tempo:** o 7B levou o dobro do tempo por caso.
- Um teste de plausibilidade (resposta entre 1 e o prazo) pegaria o 3B em 4 dos 10 casos. É uma ideia para o roteador entre modelos, mas não basta sozinha.

### Limitações

Apenas 10 casos, uma execução por caso, só modelos open locais, e o método de cálculo ainda não foi avaliado caso a caso. Um primeiro teste manual mostrou o 7B acertando o número final com dois erros de conta que se compensaram.

## Como reproduzir

```
pip install requests
ollama pull qwen2.5:3b
ollama pull qwen2.5
python benchmark.py
```

Os resultados vão para `results/resultados_casos.csv`, com as respostas completas em `results/*.txt`. O script retoma de onde parou se for interrompido.

## Roadmap

- [x] Teste padronizado com parâmetros fixos
- [x] Script automatizado e 10 casos de renda fixa
- [ ] Subir para 30 casos
- [ ] Comparação com API de topo e API barata (custo por 1.000 tarefas)
- [ ] Roteador entre modelos com checagem de plausibilidade
- [ ] Casos com documentos reais (lâminas de fundos, CVM)
- [ ] Servidor MCP expondo o benchmark
- [ ] Post com os resultados
