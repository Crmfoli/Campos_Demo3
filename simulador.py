# -*- coding: utf-8 -*-
# ===================================================================================
#   SIMULADOR WEB (VERSÃO FINAL - DADOS DE UMIDADE POR PROFUNDIDADE)
#
#   - Lê dados da planilha 'dados_sensores.xlsx' com a nova estrutura de profundidade.
# ===================================================================================
import os
import traceback
from flask import Flask, jsonify, render_template, request
import pandas as pd

app = Flask(__name__)

# --- CONFIGURAÇÃO ---
DATA_FILE = "dados_sensores.xlsx"
dados_planilha = pd.DataFrame()
current_index = 0

# --- FUNÇÃO DE LEITURA DE DADOS ---
def carregar_dados_da_planilha():
    global dados_planilha
    try:
        if os.path.exists(DATA_FILE):
            print(f"Carregando dados do arquivo: {DATA_FILE}...")
            df = pd.read_excel(DATA_FILE)
            
            # Renomeia as colunas da sua nova planilha para um padrão interno
            df = df.rename(columns={
                'data_hora': 'timestamp',
                'profundidade 0,3 m': 'umidade_p1',
                'profundidade 0,8 m': 'umidade_p2',
                'profundidade 1,5 m': 'umidade_p3',
                'profundidade 2,0 m': 'umidade_p4',
                'profundidade 2,5 m': 'umidade_p5'
            })
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            colunas_finais = ['timestamp', 'umidade_p1', 'umidade_p2', 'umidade_p3', 'umidade_p4', 'umidade_p5']
            df = df[colunas_finais]
            
            df = df.sort_values(by='timestamp').reset_index(drop=True)
            dados_planilha = df
            print(f"Sucesso! {len(dados_planilha)} registros carregados.")
        else:
            print(f"AVISO: Arquivo '{DATA_FILE}' não encontrado.")
    except Exception:
        print(f"FALHA CRÍTICA AO LER O ARQUIVO EXCEL: {traceback.format_exc()}")

# --- ROTAS ---
@app.route('/')
def pagina_de_acesso(): return render_template('index.html')

@app.route('/mapa', methods=['GET', 'POST'])
def pagina_mapa(): return render_template('mapa.html')

@app.route('/dashboard')
def pagina_dashboard():
    device_id = request.args.get('device_id', 'Multi-Sensor Profundidade')
    return render_template('dashboard.html', device_id=device_id)

# --- ROTAS DE API ---
@app.route('/api/dados')
def api_dados():
    if dados_planilha.empty: return jsonify([])
    df_filtrado = dados_planilha.tail(30)
    dados_json = df_filtrado.to_dict(orient='records')
    for record in dados_json:
        record['timestamp'] = record['timestamp'].isoformat()
    return jsonify(dados_json)

@app.route('/api/dados_atuais')
def api_dados_atuais():
    global current_index
    if dados_planilha.empty: return jsonify({"error": "Nenhum dado carregado"}), 404
    leitura_atual = dados_planilha.iloc[current_index]
    current_index = (current_index + 1) % len(dados_planilha)
    leitura_dict = leitura_atual.to_dict()
    leitura_dict['timestamp'] = leitura_dict['timestamp'].isoformat()
    return jsonify(leitura_dict)

# --- INICIALIZAÇÃO ---
carregar_dados_da_planilha()

