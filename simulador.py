# -*- coding: utf-8 -*-
# ===================================================================================
#   SIMULADOR WEB (VERSÃO FINAL - DADOS DE UMIDADE POR PROFUNDIDADE)
#
#   - Lê dados da planilha 'dados_sensores.xlsx'.
#   - Se o arquivo não existir, cria um com dados de exemplo.
#   - Oferece uma API para consumir os dados em tempo real.
# ===================================================================================
import os
import traceback
from flask import Flask, jsonify, render_template, request
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

app = Flask(__name__)

# --- CONFIGURAÇÃO ---
DATA_FILE = "dados_sensores.xlsx"
dados_planilha = pd.DataFrame()
current_index = 0

# --- FUNÇÃO PARA CRIAR DADOS DE EXEMPLO ---
def criar_planilha_exemplo_se_nao_existir():
    """
    Verifica se o arquivo de dados existe. Se não, cria um arquivo .xlsx com dados fictícios.
    """
    if not os.path.exists(DATA_FILE):
        print(f"AVISO: Arquivo '{DATA_FILE}' não encontrado. Criando um novo com dados de exemplo...")
        try:
            # Define a estrutura das colunas
            colunas = {
                'data_hora': [],
                'profundidade 0,3 m': [],
                'profundidade 0,8 m': [],
                'profundidade 1,5 m': [],
                'profundidade 2,0 m': [],
                'profundidade 2,5 m': []
            }

            # Gera 200 registros de dados fictícios
            start_time = datetime.now() - timedelta(hours=200)
            for i in range(200):
                colunas['data_hora'].append(start_time + timedelta(hours=i))
                # Gera valores de umidade com alguma variação
                colunas['profundidade 0,3 m'].append(round(np.random.uniform(25.0, 35.0) + np.sin(i/10.0) * 5, 2))
                colunas['profundidade 0,8 m'].append(round(np.random.uniform(30.0, 40.0) + np.sin(i/12.0) * 4, 2))
                colunas['profundidade 1,5 m'].append(round(np.random.uniform(38.0, 45.0) + np.sin(i/15.0) * 3, 2))
                colunas['profundidade 2,0 m'].append(round(np.random.uniform(42.0, 48.0), 2))
                colunas['profundidade 2,5 m'].append(round(np.random.uniform(45.0, 50.0), 2))

            # Cria o DataFrame e salva como arquivo Excel
            df_exemplo = pd.DataFrame(colunas)
            df_exemplo.to_excel(DATA_FILE, index=False)
            print(f"Sucesso! Arquivo '{DATA_FILE}' criado com 200 registros.")

        except Exception as e:
            print(f"FALHA CRÍTICA AO CRIAR O ARQUIVO DE EXEMPLO: {e}")
            print(traceback.format_exc())


# --- FUNÇÃO DE LEITURA DE DADOS ---
def carregar_dados_da_planilha():
    global dados_planilha
    try:
        if os.path.exists(DATA_FILE):
            print(f"Carregando dados do arquivo: {DATA_FILE}...")
            df = pd.read_excel(DATA_FILE)

            # DEBUG: Mostra as colunas lidas do arquivo para facilitar a verificação
            print("\n--- INFORMAÇÕES DO ARQUIVO EXCEL ---")
            print("Colunas encontradas no arquivo:")
            print(list(df.columns))
            print("-------------------------------------\n")

            # Mapeamento das colunas esperadas para as colunas internas
            mapa_colunas = {
                'data_hora': 'timestamp',
                'profundidade 0,3 m': 'umidade_p1',
                'profundidade 0,8 m': 'umidade_p2',
                'profundidade 1,5 m': 'umidade_p3',
                'profundidade 2,0 m': 'umidade_p4',
                'profundidade 2,5 m': 'umidade_p5'
            }
            
            # Renomeia as colunas
            df = df.rename(columns=mapa_colunas)

            # Converte a coluna de data/hora
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Seleciona e reordena apenas as colunas necessárias
            colunas_finais = ['timestamp', 'umidade_p1', 'umidade_p2', 'umidade_p3', 'umidade_p4', 'umidade_p5']
            df = df[colunas_finais]

            # Ordena os dados por data e reinicia o índice
            df = df.sort_values(by='timestamp').reset_index(drop=True)
            dados_planilha = df
            print(f"Sucesso! {len(dados_planilha)} registros carregados.")
        else:
            print(f"AVISO: Arquivo '{DATA_FILE}' não encontrado.")
    except KeyError as e:
        print(f"\nFALHA CRÍTICA: ERRO DE CHAVE (KeyError) - {e}")
        print("Isso geralmente significa que um nome de coluna esperado no código não foi encontrado no arquivo Excel.")
        print("Verifique se as colunas no seu arquivo .xlsx correspondem exatamente a estas: ['data_hora', 'profundidade 0,3 m', ...]\n")
    except Exception:
        print(f"FALHA CRÍTICA AO LER O ARQUIVO EXCEL: {traceback.format_exc()}")

# --- ROTAS DO SITE ---
@app.route('/')
def pagina_de_acesso():
    return render_template('index.html')

@app.route('/mapa', methods=['GET', 'POST'])
def pagina_mapa():
    return render_template('mapa.html')

@app.route('/dashboard')
def pagina_dashboard():
    device_id = request.args.get('device_id', 'Multi-Sensor Profundidade')
    return render_template('dashboard.html', device_id=device_id)

# --- ROTAS DE API (PARA FORNECER DADOS) ---
@app.route('/api/dados')
def api_dados():
    """ Retorna os últimos 30 registros. """
    if dados_planilha.empty:
        return jsonify([])
        
    df_filtrado = dados_planilha.tail(30)
    dados_json = df_filtrado.to_dict(orient='records')
    # Converte o timestamp para formato ISO para ser compatível com JSON
    for record in dados_json:
        record['timestamp'] = record['timestamp'].isoformat()
    return jsonify(dados_json)

@app.route('/api/dados_atuais')
def api_dados_atuais():
    """ Simula uma leitura em tempo real, retornando um registro por vez. """
    global current_index
    if dados_planilha.empty:
        return jsonify({"error": "Nenhum dado carregado"}), 404

    # Pega o registro atual e avança o índice
    leitura_atual = dados_planilha.iloc[current_index]
    current_index = (current_index + 1) % len(dados_planilha) # Volta ao início quando chega ao fim

    # Converte para dicionário e ajusta o formato da data
    leitura_dict = leitura_atual.to_dict()
    leitura_dict['timestamp'] = leitura_dict['timestamp'].isoformat()
    
    return jsonify(leitura_dict)

# --- INICIALIZAÇÃO ---
if __name__ == '__main__':
    criar_planilha_exemplo_se_nao_existir()
    carregar_dados_da_planilha()
    app.run(debug=True, port=5000)


