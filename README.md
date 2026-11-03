# Custo × Qualidade em IA financeira

Quanto custa, e quanto de qualidade se perde, ao trocar um modelo de API de topo por um modelo mais barato ou por um modelo open rodando localmente em tarefas de renda fixa?

Projeto em andamento. Este repositório registra o benchmark passo a passo.

## Experimento 1: duration de Macaulay (30 casos, modelos open locais)

**Tarefa:** calcular a duration de Macaulay de um título prefixado (face R$ 1.000, cupom anual). Os 30 casos variam cupom (6-14%), prazo (3-10 anos) e taxa de desconto (4-16%): o caso 1 é o do primeiro teste e os outros 29 são sorteados com seed fixa. O gabarito é calculado por código.

**Ambiente:** Windows, só CPU (Intel Iris Xe integrada, 24 GB de RAM), modelos via [Ollama](https://ollama.com). Temperatura 0, seed 42, limite de 4.000 tokens por resposta, mesmo prompt para todos.

| Métrica | qwen2.5 3B | qwen2.5 7B |
|---|---|---|
| Acertos (erro ≤ 1%) | 0/30 | 8/30 |
| Acertos (erro ≤ 5%) | 0/30 | 14/30 |
| Acertos (erro ≤ 25%) | 6/30 | 19/30 |
| Erro mediano | 42,8% | 10,8% |
| Respostas impossíveis* | 10/30 | 0/30 |
| Sem resposta no formato | 3 (1 cortada pelo limite de tokens) | 0 |
| Tempo médio por caso** | 150 s | 265 s |
| Velocidade média** | 10,0 tok/s | 5,0 tok/s |

\* A duration de Macaulay de um título com cupom anual está sempre entre 1 e o prazo. Resposta fora disso é impossível.
\** Medido com o computador em uso e com grande variação entre lotes (3B: 7,7 a 11,1 tok/s; 7B: 3,4 a 5,8). Tratar como indicativo.

### O que os dados mostram

- **3B não serve para essa tarefa:** nenhum caso com erro menor que 10%, 10 respostas impossíveis e valores absurdos (ex.: 305 anos para um título de menos de 3 anos). O erro médio dele (626%) é distorcido por essas respostas, por isso a tabela usa a mediana.
- **7B acerta quase metade dentro de 5% (14/30), mas em 11 dos 30 casos o erro passa de 25%.** Nunca deu resposta impossível.
- **Prazo curto ajuda o 7B:** 9 de 13 casos de 3 a 5 anos ficaram a até 5% de erro, contra 5 de 17 casos de 6 anos ou mais (amostra pequena).
- **Amostra pequena engana:** nos 10 primeiros casos o 7B parecia bem melhor (4/10 a 1%, mediana de 2,4%). Com 30, caiu para 8/30 e mediana de 10,8%.
- **Teste de plausibilidade (resposta entre 1 e o prazo):** pega 10 dos erros do 3B, mas outras 12 respostas dele estavam dentro do intervalo e erradas por mais de 25%. Sozinho, não basta para um roteador entre modelos.

### Limitações

30 casos, uma execução por caso, só modelos open locais e só duration de Macaulay com cupom anual. Avaliei o número final, não o método de cálculo caso a caso (um teste manual inicial mostrou o 7B acertando o número com dois erros de conta que se compensaram).

## Como reproduzir

```
pip install requests
ollama pull qwen2.5:3b
ollama pull qwen2.5
python benchmark.py
```

Os resultados vão para `results/resultados_casos.csv`, com as respostas completas em `results/*.txt`. O script limita o tamanho das respostas, registra falhas sem parar e retoma de onde parou se for interrompido.

## Roadmap

- [x] Teste padronizado com parâmetros fixos
- [x] Script automatizado e 30 casos de renda fixa
- [ ] Comparação com API de topo e API barata (custo por 1.000 tarefas)
- [ ] Roteador entre modelos
- [ ] Casos com documentos reais (lâminas de fundos, CVM)
- [ ] Servidor MCP expondo o benchmark
- [ ] Post com os resultados
