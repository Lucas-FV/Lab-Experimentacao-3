import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, mannwhitneyu
import os

# 1. Carregar os dados
print("Carregando o dataset...")
df = pd.read_csv('../ColetaDados/dataset_prs_lab03.csv')

# Criar pasta para salvar os gráficos
if not os.path.exists('graficos'):
    os.makedirs('graficos')

print("\n" + "="*50)
print("RELATÓRIO ESTATÍSTICO - SPRINT 3")
print("="*50)

# ==========================================
# DIMENSÃO A: FEEDBACK FINAL (MERGED vs CLOSED)
# ==========================================
print("\n--- DIMENSÃO A: Medianas por Status ---")
# O laboratório exige a sumarização usando os valores medianos.
colunas_analise = ['tamanho_arquivos', 'linhas_adicionadas', 'linhas_removidas', 
                   'tempo_analise_horas', 'tamanho_descricao', 'participantes', 'comentarios']

medias_status = df.groupby('status')[colunas_analise].median()
print(medias_status)

print("\n--- Teste Mann-Whitney U (Diferença entre MERGED e CLOSED) ---")
# Justificativa: Como Status é categórico e os dados não são normais, usamos Mann-Whitney.
for col in colunas_analise:
    merged = df[df['status'] == 'MERGED'][col]
    closed = df[df['status'] == 'CLOSED'][col]
    
    # Executa o teste estatístico
    stat, p = mannwhitneyu(merged, closed, alternative='two-sided')
    significativo = "SIM" if p < 0.05 else "NÃO"
    print(f"{col}: p-valor = {p:.5f} (Diferença Significativa? {significativo})")

# Gráficos Dimensão A (Boxplots)
sns.set_theme(style="whitegrid")
for col in colunas_analise:
    plt.figure(figsize=(8, 6))
    # Usamos showfliers=False para esconder outliers extremos que "esmagam" o gráfico
    sns.boxplot(x='status', y=col, data=df, palette='Set2', showfliers=False)
    plt.title(f'Distribuição de {col.replace("_", " ").title()} por Status do PR')
    plt.xlabel('Status do PR')
    plt.ylabel(col.replace("_", " ").title())
    plt.savefig(f'graficos/boxplot_{col}.png', dpi=300)
    plt.close()

# ==========================================
# DIMENSÃO B: NÚMERO DE REVISÕES
# ==========================================
print("\n--- DIMENSÃO B: Correlação com Número de Revisões ---")
# Justificativa do Teste: Correlação de Spearman é usada porque métricas 
# de software (linhas de código, tempo) formam distribuições de cauda longa, não normais.
print("Teste Estatístico Escolhido: Correlação de Spearman\n")

for col in colunas_analise:
    corr, p = spearmanr(df[col], df['revisoes'])
    
    # Interpretação da força da correlação (Regra de Cohen)
    forca = "Muito Fraca"
    if abs(corr) >= 0.7: forca = "Forte"
    elif abs(corr) >= 0.5: forca = "Moderada"
    elif abs(corr) >= 0.3: forca = "Fraca"
    
    sig = "Significativo" if p < 0.05 else "Não Significativo"
    
    print(f"RQ - {col} vs Revisões:")
    print(f"  Correlação: {corr:.3f} ({forca}) | P-valor: {p:.5f} ({sig})")

# Gráficos Dimensão B (Gráficos de Dispersão / Scatter plots)
for col in colunas_analise:
    plt.figure(figsize=(8, 6))
    # Alpha reduzido ajuda a ver densidade quando há muitos pontos sobrepostos
    sns.scatterplot(x=col, y='revisoes', data=df, alpha=0.3, color='blue')
    plt.title(f'Correlação: {col.replace("_", " ").title()} vs Número de Revisões')
    plt.xlabel(col.replace("_", " ").title())
    plt.ylabel('Número de Revisões')
    
    # Aplicando escala logarítmica se houver grande variação nos eixos
    if df[col].max() > 1000:
        plt.xscale('log')
        plt.xlabel(f'{col.replace("_", " ").title()} (Escala Log)')
        
    plt.savefig(f'graficos/scatter_{col}_vs_revisoes.png', dpi=300)
    plt.close()

print("\n" + "="*50)
print("Análise concluída! Os gráficos foram salvos na pasta 'graficos/'.")
print("="*50)