# Custo × Qualidade em IA financeira

Quanto custa, e quanto de qualidade se perde, ao trocar um modelo de API de topo por um modelo mais barato ou por um modelo open rodando localmente em tarefas de renda fixa?

Projeto em andamento. Este repositório registra o benchmark passo a passo.

## Primeiro experimento (01/11/2026)

**Tarefa:** calcular a duration de Macaulay de um título prefixado (face R$ 1.000, cupom de 10% a.a. pago anualmente, 5 anos, desconto de 5% a.a.). Gabarito: **4,25 anos** (duration modificada: 4,05).

**Ambiente:** Windows, CPU apenas (Intel Iris Xe integrada, 24 GB de RAM), modelos rodando via [Ollama](https://ollama.com).

**Parâmetros fixos:** temperatura 0, seed 42, mesmo prompt para todos os modelos.

| Modelo | Resposta | Erro | Tempo total | Velocidade | Método certo? |
|---|---|---|---|---|---|
| qwen2.5:3b | 5,13 anos | 20,6% | 2m29 | 10,7 tok/s | Não |
| qwen2.5 (7B) | 4,25 anos | 0,07% | 4m26 | 4,6 tok/s | Parcial |

### Observações

- **3B:** conhece a fórmula, mas monta os fluxos de caixa errados (valores negativos, principal misturado com cupom, descontos que não batem).
- **7B:** acerta a estrutura (fluxos, tabela, fórmula), mas erra a aritmética: esqueceu o último cupom (fluxo do ano 5 deveria ser R$ 1.100) e errou um desconto. O número final bateu em parte porque os erros se compensaram, por isso "Parcial".
- Um único caso não prova nada. Uma rodada anterior do 3B, sem parâmetros fixos, deu 4,5 anos, e a seguinte deu 5,13. Isso reforça a necessidade de testar dezenas de casos.

### Prompt padrão

```
Título prefixado: valor de face R$ 1.000, cupom de 10% ao ano pago anualmente, vencimento em 5 anos, taxa de desconto de 5% ao ano. Calcule a duration de Macaulay, em anos. Mostre a tabela de fluxos descontados e termine com uma linha no formato: RESPOSTA: X anos
```

### Como reproduzir

```
ollama run qwen2.5:3b --verbose
/set parameter temperature 0
/set parameter seed 42
(cole o prompt padrão)
```

## Métricas (as mesmas em todo o benchmark)

| Métrica | Como medir |
|---|---|
| Erro no número | (resposta − gabarito) ÷ gabarito |
| Método certo? | Sim / Parcial / Não (descontou os fluxos e ponderou por prazo?) |
| Tempo total | `total duration` do Ollama |
| Velocidade | `eval rate` (tokens por segundo) |
| Custo | por 1.000 tarefas (a definir para APIs) |

## Roadmap

- [ ] Gabarito com 30-50 casos financeiros
- [ ] Comparação com API de topo e API barata
- [ ] Roteador entre modelos e economia medida
- [ ] Servidor MCP expondo o benchmark
- [ ] Post com os resultados
