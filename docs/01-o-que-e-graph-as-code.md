# 1. O que é Graph-as-Code

> A intuição do método, sem código. Se você nunca viu isso, comece aqui.

---

## O problema

Imagine uma rede de artigos científicos. Cada artigo é um **nó**. Se um artigo cita
outro, existe uma **aresta** entre eles. Cada artigo tem um texto (título e resumo) e
pertence a uma **classe** (a área dele: redes neurais, teoria, etc.).

A tarefa: descobrir a classe de um artigo olhando o texto dele e as conexões com os
vizinhos. Isso se chama **classificação de nós**.

Complicação do mundo real: quase nenhum nó vem rotulado. Você tem a classe de talvez 5%
ou 10% dos nós e precisa descobrir o resto. Rotular à mão é caro.

---

## A pergunta central

LLMs (como o ChatGPT) são ótimos com texto. Grafos misturam texto (o conteúdo de cada
nó) com estrutura (quem se conecta com quem). A pergunta que o método responde é:

> Qual a melhor forma de um LLM interagir com dados de grafo?

A resposta ingênua seria: "escreva o grafo inteiro no prompt e peça a resposta". O
problema é que grafos reais são grandes. Descrever todos os nós e todas as arestas
estoura o limite de texto que o LLM aceita (a "janela de contexto"). E mesmo quando
cabe, fica caro e o LLM se perde.

---

## A ideia do Graph-as-Code

Em vez de **descrever** o grafo para o LLM, você deixa o LLM **investigar** o grafo
sozinho, como um detetive com acesso a um terminal.

Concretamente: o grafo vira uma tabela (um DataFrame do pandas). Cada linha é um nó,
com três colunas:

| coluna | o que guarda |
|--------|--------------|
| `features` | o texto do nó (título + resumo do artigo) |
| `neighbors` | a lista de vizinhos (quem ele cita / quem o cita) |
| `label` | a classe, **se** for um dos poucos nós conhecidos; senão fica vazio |

O LLM não recebe a tabela inteira. Ele recebe só a **descrição** dela (o "schema") e a
tarefa: "descubra a classe do nó 133". A partir daí, o LLM faz perguntas em forma de
código, uma de cada vez:

```
LLM: "quero ver o texto do nó 133"   ->  escreve:  df.loc[133, 'features']
Python responde com o texto.

LLM: "quais as classes dos vizinhos?" ->  escreve:  df.loc[df.loc[133,'neighbors'], 'label'].value_counts()
Python responde:  {classe 5: 4 vizinhos, classe 1: 1 vizinho}

LLM: "já sei o suficiente"            ->  responde:  Answer 5
```

O LLM decide **o que** investigar (a parte criativa). O Python garante que a resposta é
**exata** (a parte confiável, porque LLM erra conta e o Python não).

---

## Por que isso é esperto

1. **Economia.** O LLM consulta só o que precisa. Não serializa o grafo inteiro. Em
   grafos grandes, isso é a diferença entre caber e não caber no prompt.
2. **Precisão.** Contar vizinhos de uma classe é uma operação que o Python faz sem errar.
   O LLM sozinho contaria "de cabeça" e poderia errar.
3. **Explicável.** O código que o LLM gerou é o próprio registro do raciocínio dele.
   Você consegue auditar cada passo.
4. **Flexível.** Se o texto do nó for vago, o LLM se apoia nos vizinhos. Se os vizinhos
   não tiverem rótulo, ele se apoia no texto. Usa o sinal mais informativo que tiver.

---

## O que Graph-as-Code NÃO é

- Não é uma rede neural de grafo (GNN) treinada. Não há treino: o LLM é usado direto (zero-shot) nas condições originais, sem necessidade de finetuning ou demais otimizações.
- Não é uma bala de prata : é lento (segundos a minutos por nó) e não vence uma GNN bem treinada, quando você tem muitos rótulos. Ele brilha quando há **poucos rótulos**, **poucos recursos** para treinar, ou quando precisamos de **explicabilidade**.

---

## Próximo passo

Agora que você tem a intuição, veja o mecanismo detalhado com um exemplo real em
[`02-como-funciona-passo-a-passo.md`](02-como-funciona-passo-a-passo.md).
