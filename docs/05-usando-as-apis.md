# 5. Usando as APIs de LLM

> Como o código fala com o modelo, onde trocar de provedor, e por que a estrutura é
> essa. Depois de ler, você troca de OpenRouter para OpenAI ou Ollama sem tocar no método.

---

## A ideia: um contrato, vários provedores

O método não conhece nenhum provedor específico. Ele só sabe conversar com uma função
que obedece a um contrato. Esse contrato está definido em `graph_as_code.py` como o
`Protocol` chamado `ClienteLLM`:

```python
def cliente(
    mensagens: list[Mensagem], *, temperatura: float = 0.0, seed: int = 42
) -> tuple[str | None, Uso]:
    ...
```

Em palavras: um cliente recebe o histórico da conversa e devolve dois valores, a
resposta do modelo (ou `None` se falhar) e a contagem de tokens (`Uso`).

Qualquer função com essa assinatura serve. É isso que desacopla o método do provedor:
o classificador chama `self.cliente(dialogo)` sem se importar se por trás está o
OpenRouter, a OpenAI, o Ollama ou outro serviço.

---

## Os clientes prontos

O arquivo já traz três fábricas de cliente. Cada uma devolve uma função no formato do
contrato.

### OpenRouter (o padrão do projeto)

```python
from graph_as_code import criar_cliente_openrouter

cliente = criar_cliente_openrouter(modelo="openai/o4-mini")
```

Lê a chave da variável de ambiente `OPENROUTER_API_KEY`. O OpenRouter é uma API
compatível com a da OpenAI que dá acesso a vários modelos com uma única chave, por isso
é o provedor usado por padrão aqui. Os nomes de modelo levam o prefixo do provedor de
origem, por exemplo `openai/o4-mini` ou `deepseek/deepseek-chat`.

### OpenAI (direto)

```python
from graph_as_code import criar_cliente_openai

cliente = criar_cliente_openai(modelo="o4-mini")
```

Lê a chave de `OPENAI_API_KEY`. Use quando tiver uma conta na própria OpenAI. Por baixo,
o cliente do OpenRouter reaproveita este, apenas trocando a chave e a URL base.

### Ollama (local, sem custo)

```python
from graph_as_code import criar_cliente_ollama

cliente = criar_cliente_ollama(modelo="qwen2.5:14b")
```

Fala com o servidor local do Ollama (padrão `http://localhost:11434`). Não usa chave.

---

## Onde trocar de provedor

Em um ponto só: onde você cria o cliente. O resto do código não muda.

```python
from graph_as_code import (
    ClassificadorGraphAsCode,
    criar_cliente_openrouter,
    criar_cliente_openai,
    criar_cliente_ollama,
)

# Troque APENAS esta linha para mudar de provedor:
cliente = criar_cliente_openrouter(modelo="openai/o4-mini")   # padrão do projeto
# cliente = criar_cliente_openai(modelo="o4-mini")
# cliente = criar_cliente_ollama(modelo="qwen2.5:14b")

classificador = ClassificadorGraphAsCode(cliente, classes={0: "Real", 1: "Fake"})
resultado = classificador.classificar(df, no=133)
```

No `exemplo_cora.py`, essa escolha está exposta na linha de comando (`--provedor` e
`--modelo`), e a troca acontece dentro da função `criar_cliente`.

---

## Por que a estrutura é essa

- **Testabilidade.** Como o cliente é só uma função, dá para escrever um cliente falso
  (que devolve respostas fixas) e testar o método sem gastar API nem depender de rede.
- **Trocar de modelo é barato.** Comparar o4-mini com um modelo local vira uma questão
  de trocar uma linha, o que é exatamente o tipo de experimento que interessa aqui.
- **O método fica limpo.** O laço de classificação não tem `if provedor == ...`
  espalhado. Toda a especificidade de cada API fica isolada na sua fábrica de cliente.

---

## Escrever seu próprio cliente

Precisa de um provedor que não está aqui? Escreva uma função no formato do contrato:

```python
from graph_as_code import Mensagem, Uso

def meu_cliente(mensagens: list[Mensagem], *, temperatura: float = 0.0, seed: int = 42):
    texto = chamar_meu_servico(mensagens, temperatura=temperatura)
    uso = Uso(prompt=..., completion=...)   # preencha se o serviço reportar tokens
    return texto, uso
```

E use normalmente:

```python
classificador = ClassificadorGraphAsCode(meu_cliente, classes)
```

---

## Configuração por variáveis de ambiente

As chaves ficam em um arquivo `.env` (nunca versionado). Copie o modelo e preencha:

```bash
cp .env.example .env
# edite .env e coloque a chave do provedor que for usar
```

O `.env.example` traz as variáveis com valor vazio, para você preencher só a que
precisar. Nunca coloque a chave real no código nem faça commit dela.
