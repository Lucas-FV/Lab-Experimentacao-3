import requests
import pandas as pd
from datetime import datetime
import time
import sys
import os

# Substitua pelo seu NOVO Personal Access Token (Classic) com permissão 'public_repo'
GITHUB_TOKEN = ''
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

# Query parametrizada para buscar PRs de um repositório específico
# Reduzido para 20 para evitar o erro de conexão cortada em repositórios muito pesados
PR_QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(first: 20, states: [MERGED, CLOSED], orderBy: {field: CREATED_AT, direction: DESC}, after: $cursor) {
      pageInfo {
        endCursor
        hasNextPage
      }
      nodes {
        state
        createdAt
        closedAt
        mergedAt
        bodyText
        additions
        deletions
        changedFiles
        participants { totalCount }
        comments { totalCount }
        reviews { totalCount }
      }
    }
  }
}
"""

def extract_prs_from_repo(owner, name, max_prs=150):
    prs_data = []
    cursor = None
    
    while len(prs_data) < max_prs:
        variables = {"owner": owner, "name": name, "cursor": cursor}
        
        # Tratamento de rede para não quebrar o script se a conexão cair
        try:
            response = requests.post('https://api.github.com/graphql', json={'query': PR_QUERY, 'variables': variables}, headers=HEADERS, timeout=30)
        except requests.exceptions.ChunkedEncodingError:
            print(f"\n[!] Conexão cortada pelo GitHub (ChunkedEncodingError) em {owner}/{name}. Repositório muito pesado. Pulando...")
            break
        except requests.exceptions.RequestException as e:
            print(f"\n[!] Falha de rede ao acessar {owner}/{name}: {e}. Pulando...")
            break
        
        # Tratamento atualizado para erros de servidor (como o 502)
        if response.status_code != 200:
            print(f"\n[!] Erro {response.status_code} no servidor do GitHub ao acessar {owner}/{name}.")
            print("O repositório pode estar muito pesado ou indisponível no momento. Pulando para o próximo...")
            break
            
        # Tratamento de erro caso o retorno não seja um JSON válido (ex: página HTML de erro do Nginx)
        try:
            data = response.json()
        except ValueError:
            print(f"\n[!] O GitHub não retornou um JSON válido para {owner}/{name}. Pulando...")
            break
            
        if 'errors' in data or not data.get('data') or not data['data'].get('repository'):
            print(f"  -> Repositório não encontrado ou erro na query. Pulando...")
            break
            
        pr_nodes = data['data']['repository']['pullRequests']
        
        for pr in pr_nodes['nodes']:
            # Regra: Pelo menos uma revisão [cite: 34]
            if pr['reviews']['totalCount'] < 1:
                continue
                
            # Cálculo de tempo (em horas)
            created_at = datetime.fromisoformat(pr['createdAt'].replace('Z', '+00:00'))
            end_time_str = pr['mergedAt'] if pr['state'] == 'MERGED' else pr['closedAt']
            
            if end_time_str:
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                time_diff_hours = (end_time - created_at).total_seconds() / 3600
                
                # Regra: Revisão levou pelo menos 1 hora (remover bots) [cite: 35]
                if time_diff_hours > 1:
                    prs_data.append({
                        'repositorio': f"{owner}/{name}",
                        'status': pr['state'],
                        'tamanho_arquivos': pr['changedFiles'],
                        'linhas_adicionadas': pr['additions'],
                        'linhas_removidas': pr['deletions'],
                        'tempo_analise_horas': round(time_diff_hours, 2),
                        'tamanho_descricao': len(pr['bodyText']) if pr['bodyText'] else 0,
                        'participantes': pr['participants']['totalCount'],
                        'comentarios': pr['comments']['totalCount'],
                        'revisoes': pr['reviews']['totalCount']
                    })
            
            if len(prs_data) >= max_prs:
                break
                
        cursor = pr_nodes['pageInfo']['endCursor']
        if not pr_nodes['pageInfo']['hasNextPage']:
            break
            
    return prs_data

# Execução principal
print("Lendo a lista de repositórios...")

# Validação do caminho do arquivo CSV
try:
    df_repos = pd.read_csv('../Repositories/repositorios.csv')
except FileNotFoundError:
    print("ERRO: O arquivo '../Repositories/repositorios.csv' não foi encontrado.")
    print("Verifique se você está rodando o script de dentro da pasta 'ColetaDados' e se o CSV existe.")
    sys.exit()

ARQUIVO_SAIDA = 'dataset_prs_lab03.csv'
total_coletado = 0

# Remove o arquivo de saída antigo se existir, para não misturar execuções
if os.path.exists(ARQUIVO_SAIDA):
    os.remove(ARQUIVO_SAIDA)

# Iterando sobre a lista de repositórios
for index, row in df_repos.iterrows():
    # Limpeza de espaços em branco invisíveis e garantia de que é uma string
    repo_full_name = str(row['repositorio']).strip() 
    
    # Prevenção contra linhas vazias ou mal formatadas no CSV
    if not repo_full_name or '/' not in repo_full_name:
        continue
        
    owner, name = repo_full_name.split('/')
    
    print(f"[{index+1}/{len(df_repos)}] Coletando PRs de {owner}/{name}...")
    prs = extract_prs_from_repo(owner, name)
    
    # SALVAMENTO CONTÍNUO: Salva no CSV a cada repositório concluído
    if prs:
        df_temp = pd.DataFrame(prs)
        # O mode='a' anexa os dados. O header só é colocado na primeira vez.
        df_temp.to_csv(ARQUIVO_SAIDA, mode='a', header=not os.path.exists(ARQUIVO_SAIDA), index=False)
        total_coletado += len(prs)
        
    time.sleep(1) # Proteção contra rate limit da API

print(f"\nColeta finalizada com sucesso! Arquivo '{ARQUIVO_SAIDA}' gerado com {total_coletado} PRs válidos no total.")