# 2. Como funciona, passo a passo

> O mecanismo do método com um exemplo real de classificação de um nó.

---

## O grafo como tabela

O primeiro passo é representar o grafo como um DataFrame do pandas. Cada linha é um
nó. Veja um recorte de um grafo de artigos:

| id | features (texto) | label (classe) | neighbors (conexões) |
|----|------------------|----------------|----------------------|
| 133 | "A Reinforcement Learning Approach..." | ? | [134, 135, 707, 2048] |
| 134 | "Q-Learning for Robot..." | 5 | [133, 135] |
| 135 | "Policy Gradient Methods..." | 5 | [133, 134, 707] |
| 707 | "Temporal Difference..." | 5 | [133, 135] |
| 2048 | "Image Segmentation..." | 1 | [133] |

O nó 133 é o alvo: queremos descobrir a classe dele (o `?`). Alguns vizinhos já têm
rótulo visível (134, 135, 707 são classe 5; o 2048 é classe 1).

---

## O laço de investigação

O LLM recebe apenas a descrição da tabela e a tarefa. Então ele investiga em rodadas.
Cada rodada tem a forma: o LLM raciocina, escreve uma expressão pandas, o Python
executa e devolve o resultado.

### Passo 1: "sobre o que é este nó?"

O LLM escreve:

```python
df.loc[133, 'features']
```

O Python responde:

```
"A Reinforcement Learning Approach to Job-Shop Scheduling"
```

Agora o LLM sabe: o texto fala de Reinforcement Learning. Hipótese inicial: classe 5.

### Passo 2: "o que os vizinhos dizem?"

O LLM escreve:

```python
df.loc[df.loc[133, 'neighbors'], 'label'].value_counts()
```

O Python responde:

```
{5: 4, 1: 1}
```

Quatro dos cinco vizinhos são classe 5. A vizinhança confirma a hipótese.

### Passo 3: decidir

O LLM combina os dois sinais (texto sugere classe 5, vizinhança confirma classe 5) e
responde:

```
Answer 5
```

Correto. Bastaram duas consultas, sem nunca carregar o grafo inteiro.

---

## Por que funciona

- **O LLM escolhe o que investigar.** Essa é a parte criativa: decidir que perguntas
  fazer. Um nó com texto claro pode nem precisar olhar os vizinhos.
- **O Python garante a resposta exata.** Contar quantos vizinhos são de cada classe é
  uma operação determinística. O LLM sozinho poderia errar a contagem; delegar ao
  Python elimina esse erro.
- **Os sinais se complementam.** Se o texto fosse ambíguo, a vizinhança desempataria.
  Se os vizinhos não tivessem rótulo, o texto sustentaria a decisão sozinho.

---

## Onde isso está no código

Tudo isso vive em `codigo/graph_as_code.py`, em quatro blocos:

| Bloco | Classe/função | O que faz |
|-------|---------------|-----------|
| 1. Prompt | `montar_prompt_sistema` | descreve a tabela e a tarefa ao LLM |
| 2. Executor | `ExecutorSeguro` | roda a expressão pandas num sandbox seguro |
| 3. Extração | `extrair_codigo`, `extrair_resposta` | lê a resposta do LLM |
| 4. Classificador | `ClassificadorGraphAsCode` | orquestra o laço acima |

O laço do passo a passo está no método `classificar`. Leia o arquivo: ele foi escrito
para ser lido de cima para baixo, na mesma ordem em que o método pensa.

---

## Uma nota sobre segurança

O LLM gera código que **nós executamos**. Deixar código arbitrário rodar seria
perigoso. Por isso o `ExecutorSeguro` valida a expressão antes de rodar: ele analisa a
árvore sintática e recusa qualquer coisa que não seja consulta a DataFrame. Nada de
`import`, `open`, `eval` ou acesso ao sistema. Também há um tempo limite por expressão.

---

## Próximo passo

[`03-reproduzir-do-zero.md`](03-reproduzir-do-zero.md).
