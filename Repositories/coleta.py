import requests
import pandas as pd
from datetime import datetime
import time

# Substitua pelo seu Personal Access Token
GITHUB_TOKEN = 'SEU_TOKEN_AQUI'
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

# Query parametrizada para buscar PRs de um repositório específico
PR_QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(first: 100, states: [MERGED, CLOSED], orderBy: {field: CREATED_AT, direction: DESC}, after: $cursor) {
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
        response = requests.post('https://api.github.com/graphql', json={'query': PR_QUERY, 'variables': variables}, headers=HEADERS)
        
        if response.status_code != 200:
            print(f"Erro ao acessar {owner}/{name}. Pulando...")
            break
            
        data = response.json()
        if 'errors' in data or not data['data']['repository']:
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

# Execução principal do Membro 2
print("Lendo a lista de repositórios...")
df_repos = pd.read_csv('repositorios.csv')
dataset_final = []

# Iterando sobre a lista gerada pelo Membro 1
for index, row in df_repos.iterrows():
    repo_full_name = row['repositorio']
    owner, name = repo_full_name.split('/')
    
    print(f"[{index+1}/{len(df_repos)}] Coletando PRs de {repo_full_name}...")
    prs = extract_prs_from_repo(owner, name)
    dataset_final.extend(prs)
    time.sleep(1) # Proteção contra rate limit

# Salvando o dataset completo da Sprint 1 
df_final = pd.DataFrame(dataset_final)
df_final.to_csv('dataset_prs_lab03.csv', index=False)
print(f"Coleta finalizada! Dataset gerado com {len(df_final)} PRs válidos.")