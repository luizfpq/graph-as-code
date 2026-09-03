# 4. A genealogia do método

> De onde o Graph-as-Code veio. Cada trabalho abaixo resolve uma limitação do anterior.

---

## A ideia em uma linha

O Graph-as-Code não surgiu do nada. Ele é a convergência de cinco anos de pesquisa
sobre como fazer um LLM raciocinar melhor. Vale conhecer a linhagem, porque ela explica
por que o método tem a forma que tem.

---

## 2022: Chain-of-Thought (CoT)

**Ideia:** se o LLM explicita o raciocínio passo a passo, ele erra menos.

Antes, você perguntava e o modelo respondia direto (e errava em problemas de vários
passos). O CoT mostrou que pedir "pense passo a passo" melhora bastante o resultado.

**Limitação:** o modelo ainda faz as contas "de cabeça". Em problemas com aritmética
mais pesada, o raciocínio em texto continua errando.

> Wei et al. (2022). Chain-of-Thought Prompting Elicits Reasoning in LLMs. NeurIPS.

---

## 2023: PAL (Program-Aided Language Models)

**Ideia:** em vez de calcular no texto, o LLM gera código que calcula.

O modelo traduz o problema em um programa Python, e o Python executa. A conta passa a
ser exata, porque quem calcula é o interpretador, não o modelo.

**Limitação:** o LLM precisa receber todos os dados no prompt para gerar o programa. Um
grafo grande não cabe na janela de contexto.

> Gao et al. (2023). PAL: Program-Aided Language Models. ICML.

---

## 2023: ReAct (Reasoning + Acting)

**Ideia:** buscar os dados sob demanda, agindo em passos (pensar, agir, observar).

Em vez de receber tudo de uma vez, o LLM chama ações que trazem só o que ele pede
naquele momento.

**Limitação:** as ações são atômicas. Uma contagem simples pode exigir muitas chamadas
(pega vizinhos, pega rótulo de cada um, soma). Fica lento e sem composição.

> Yao et al. (2023). ReAct: Synergizing Reasoning and Acting in LLMs. ICLR.

---

## 2024: CodeGraph

**Ideia:** e se o LLM gerasse código especificamente para resolver problemas sobre
grafos?

Este é o precursor direto. O CodeGraph mostrou que, dando exemplos ao LLM, ele aprende
a escrever programas que respondem perguntas sobre grafos (contar arestas, achar
caminhos), evitando os erros aritméticos e deixando o raciocínio auditável. Os autores
relataram ganhos de 1,3% a 58,6% em tarefas de raciocínio sobre grafos, dependendo da
tarefa.

**Limitação:** era uma prova de conceito. Poucos datasets, sem comparação sistemática
com outros paradigmas, sem validação em escala. E o LLM gera o programa inteiro de uma
vez, sem ver resultados intermediários.

> Cai et al. (2024). CodeGraph: Enhancing Graph Reasoning of LLMs with Code.
> arXiv:2408.13863.

---

## 2026: Graph-as-Code

**Ideia:** juntar código (do PAL e do CodeGraph) com iteração e feedback (do ReAct),
validado em escala.

O Graph-as-Code faz o LLM gerar expressões pandas para explorar o grafo, uma de cada
vez, e **cada expressão é informada pelo resultado da anterior**. Essa é a diferença
central para o CodeGraph, que gerava o programa completo sem ver resultados no meio do
caminho. O método foi avaliado em 14 datasets, com vários modelos, mostrando ganhos
grandes em grafos de texto longo ou de alto grau, justamente onde descrever o grafo no
prompt estoura o orçamento de tokens.

> Finkelshtein et al. (2026). Actions Speak Louder than Prompts. ICLR.

---

## O mapa completo

| Ano | Trabalho | Avanço | Limitação que deixou |
|-----|----------|--------|----------------------|
| 2022 | Chain-of-Thought | pensar passo a passo | conta de cabeça ainda erra |
| 2023 | PAL | delega a conta ao código | precisa de todos os dados no prompt |
| 2023 | ReAct | busca dados sob demanda | ações atômicas, sem composição |
| 2024 | CodeGraph | código aplicado a grafos | prova de conceito, sem validação |
| 2026 | Graph-as-Code | código + iteração, validado | lento; não vence GNN com muitos rótulos |

Cada linha resolve o problema da anterior. O Graph-as-Code é a convergência natural
dessa trajetória.

---

## Créditos

Todos os trabalhos acima têm referência completa em [`../CITATION.md`](../CITATION.md).
Se você usar este material, cite as fontes originais.
