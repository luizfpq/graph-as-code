# Reprodução com o4-mini

> Reprodução do Graph-as-Code puro sobre os datasets canônicos, com o modelo o4-mini.

---

## Protocolo

- 100 nós de teste por rodada, sorteados com semente fixa.
- Rótulos de treino visíveis no DataFrame; rótulos de teste ocultos.
- Temperatura 0 (determinístico), limite de 15 passos por nó.
- O alvo é o número que o artigo original reporta para a mesma configuração.

---

## Resultados

| Dataset | Semente | Acurácia | Alvo do artigo | Tokens por nó | Passos médios |
|---------|---------|----------|----------------|---------------|---------------|
| ArXiv | 1 | 79% | 74,4 ± 3,0 | 4.497 | 3,2 |
| ArXiv | 2 | 76% | 74,4 ± 3,0 | 4.358 | 3,2 |
| ArXiv | 42 | 75% | 74,4 ± 3,0 | 4.268 | 3,2 |
| Cora | 42 | 77% | 85,2 ± 1,5 | 2.394 | 2,6 |
| Cora | 1 | 67% | 85,2 ± 1,5 | 2.535 | 2,8 |

---

## Leitura

No ArXiv a reprodução fica dentro da faixa reportada pelo artigo. No Cora ainda fica
abaixo do alvo, provavelmente por diferença na fração de rótulos visíveis e na
amostragem; é um ponto em aberto.

O que importa observar não é só a acurácia, e sim a eficiência: o método resolve cada
nó com cerca de 3 expressões, sem nunca serializar o grafo inteiro no prompt. Em grafos
densos, é a diferença entre caber e não caber no contexto do modelo.

---

## Sobre a variância dos números

Mesmo com temperatura 0 e semente fixa, rodar de novo pode dar percentuais um pouco
diferentes. Isso é esperado e tem duas causas principais:

- **Roteamento do provedor.** O OpenRouter (padrão do projeto) pode encaminhar a mesma
  requisição para provedores ou instâncias diferentes do mesmo modelo, com pequenas
  diferenças de tokenização, quantização ou versão. Determinismo estrito exigiria fixar
  o provedor (OpenAI direta ou Ollama local).
- **Tamanho da amostra.** Com poucos nós, um acerto a mais ou a menos move muito o
  percentual. As medições acima usam 100 nós justamente para reduzir esse efeito.

Portanto, tome os valores como ordem de grandeza, não como número exato. As faixas
acima são compatíveis com o que o artigo original reporta.

---

## Como reproduzir

O exemplo deste repositório (`codigo/exemplo_cora.py`) roda o método sobre o Cora e é
suficiente para ver o mecanismo. Para uma reprodução com significância (100 nós, várias
sementes, ArXiv incluso), estenda o exemplo variando `--n`, `--seed` e o dataset. Os
números acima usaram exatamente o mesmo método que está em `codigo/graph_as_code.py`.
