# Créditos e como citar

Este repositório é uma reimplementação didática e independente. As ideias e os dados
pertencem aos autores originais listados abaixo. Se você usar este material, cite as
fontes originais correspondentes.

---

## O método (obrigatório citar)

**Graph-as-Code**, o método reproduzido aqui:

> Finkelshtein, B., Cucerzan, S., Jauhar, S. K., & White, R. (2026).
> *Actions Speak Louder than Prompts: A Study of Graph-as-Code for LLM Graph Reasoning.*
> International Conference on Learning Representations (ICLR 2026).

```bibtex
@inproceedings{finkelshtein2026gac,
  title     = {Actions Speak Louder than Prompts},
  author    = {Finkelshtein, Ben and Cucerzan, Silviu and Jauhar, Sujay Kumar and White, Ryen},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2026}
}
```

---

## O precursor direto (CodeGraph)

O Graph-as-Code estende a ideia de resolver problemas de grafo fazendo o LLM gerar
código, introduzida por:

> Cai, X., Wang, Z., Chen, H., Yin, D., Wu, L., & Zhang, Y. (2024).
> *CodeGraph: Enhancing Graph Reasoning of LLMs with Code.* arXiv:2408.13863.

```bibtex
@article{cai2024codegraph,
  title   = {CodeGraph: Enhancing Graph Reasoning of LLMs with Code},
  author  = {Cai, Xin and Wang, Zheng and Chen, Haixu and Yin, Dawei and Wu, Lin and Zhang, Yao},
  journal = {arXiv preprint arXiv:2408.13863},
  year    = {2024}
}
```

Nota: a diferença entre os dois está explicada em `docs/04-genealogia-do-metodo.md`. Em
resumo, o CodeGraph gera o programa inteiro de uma vez; o Graph-as-Code é iterativo, cada
expressão é informada pelo resultado da anterior.

---

## A linhagem de ideias (contexto histórico)

O método é a convergência de uma série de trabalhos. Se você citar a genealogia:

> Wei, J. et al. (2022). *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models.* NeurIPS.

> Gao, L. et al. (2023). *PAL: Program-Aided Language Models.* ICML.

> Yao, S. et al. (2023). *ReAct: Synergizing Reasoning and Acting in Language Models.* ICLR.

---

## Os datasets

**Cora** (usado no exemplo deste repositório):

> McCallum, A. K., Nigam, K., Rennie, J., & Seymore, K. (2000).
> *Automating the Construction of Internet Portals with Machine Learning.*
> Information Retrieval, 3(2), 127–163.

**OGBN-ArXiv** (usado na reprodução em `resultados/`):

> Hu, W., Fey, M., Zitnik, M., Dong, Y., Ren, H., Liu, B., Catasta, M., & Leskovec, J. (2020).
> *Open Graph Benchmark: Datasets for Machine Learning on Graphs.* NeurIPS.
> https://ogb.stanford.edu

---

## Este repositório

Se você quiser referenciar especificamente esta reimplementação didática:

> Quirino, L. F. P. (2026). *Graph-as-Code: implementação didática e reprodutível.*
> PPGCC/FACOM, Universidade Federal de Mato Grosso do Sul.
> https://github.com/luizfpq/graph-as-code

Lembre-se: citar este repo **não substitui** citar o artigo original do método
(Finkelshtein et al., 2026).
