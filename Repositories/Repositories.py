import requests
import pandas as pd
import time

# Substitua pelo seu Personal Access Token
GITHUB_TOKEN = ''
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

def get_top_repositories(total_repos=200):
    query = """
    query($cursor: String) {
      search(query: "stars:>10000 sort:stars-desc", type: REPOSITORY, first: 50, after: $cursor) {
        pageInfo {
          endCursor
          hasNextPage
        }
        nodes {
          ... on Repository {
            nameWithOwner
            stargazerCount
          }
        }
      }
    }
    """
    
    repos = []
    cursor = None
    
    while len(repos) < total_repos:
        variables = {"cursor": cursor}
        response = requests.post('https://api.github.com/graphql', json={'query': query, 'variables': variables}, headers=HEADERS)
        
        if response.status_code != 200:
            print(f"Erro na API: {response.status_code}")
            break
            
        data = response.json()['data']['search']
        
        for node in data['nodes']:
            repos.append({
                'repositorio': node['nameWithOwner'],
                'estrelas': node['stargazerCount']
            })
            if len(repos) >= total_repos:
                break
                
        cursor = data['pageInfo']['endCursor']
        if not data['pageInfo']['hasNextPage']:
            break
            
        time.sleep(1) # Pausa leve para não sobrecarregar a API
        
    return repos

# Execução
print("Iniciando coleta dos 200 repositórios mais populares...")
repos_list = get_top_repositories(200)
df_repos = pd.DataFrame(repos_list)
df_repos.to_csv('repositorios.csv', index=False)
print(f"Sucesso! Arquivo 'repositorios.csv' gerado com {len(df_repos)} repositórios.")