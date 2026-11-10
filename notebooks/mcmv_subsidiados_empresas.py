# %% [markdown]
# # Projeto Habitação MCMV: desempenho das empresas (MCMV-Subsidiado)
#
# **Objetivo:** avaliar o desempenho das construtoras e entidades responsáveis pelos empreendimentos do MCMV-Subsidiado, combinando volume, execução e risco.
#
# **Dimensões de desempenho**
# - **Volume:** valor e unidades contratadas (contexto).
# - **Execução:** proporção de unidades entregues sobre as contratadas.
# - **Risco:** proporção de unidades distratadas e de empreendimentos cancelados.
# - **Diversificação:** número de municípios, UFs e modalidades em que a empresa atua.
#
# **Métrica de proporção:** ponderada (soma das unidades da empresa dividida pelo total contratado da empresa). A média por empreendimento serve como verificação.
#
# **Base:** carregada de `src/preparacao.py`, a mesma usada na análise territorial.

# %%
import sys
from pathlib import Path

# Permite importar o módulo src/ a partir da pasta notebooks/
sys.path.append(str(Path("..").resolve()))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

from src.preparacao import carregar_base_limpa, preparar_sem_codigo

# %%
df_sub = carregar_base_limpa()
print("Linhas na base limpa:", len(df_sub))
print("Empresas (CNPJ válido):", df_sub["txt_cnpj_construtora_entidade"].nunique())
# %%
print(len(df_sub), df_sub["val_contratado_total"].sum(), df_sub["qtd_uh"].sum())
# %%
