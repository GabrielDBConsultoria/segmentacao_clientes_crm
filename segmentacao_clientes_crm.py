#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pyodbc
import pandas as pd
from datetime import datetime

# Conectar ao banco de dados MySQL via ODBC usando DSN
dsn_name = 'segvojoana'
conn = pyodbc.connect(f'DSN={dsn_name};')

# Etapa 1: Consulta para obter os dados necessários
query = """
SELECT 
    ped.ped_pescodigo, 
    ped.ped_dtemissao, 
    pes.pes_razao, 
    pes.pes_fantasia, 
    ped.ped_pesobruto, 
    pes.pes_clccodigo, 
    cli.cli_cclcodigoe, 
    ccl.ccl_desc AS carteira_cliente
FROM 
    pedidos ped
JOIN 
    pessoa pes ON ped.ped_pescodigo = pes.pes_codigo
JOIN 
    cliente cli ON pes.pes_codigo = cli.cli_pescodigo
LEFT JOIN 
    carteiracli ccl ON cli.cli_cclcodigoe = ccl.ccl_codigo
WHERE 
    ped.ped_natcodigo IN ('VEN', 'VES', 'VIN', 'VIS') 
    AND ped.ped_pescodigo <> 1 
    AND ped.ped_stpcodigo = 6
    AND ped.ped_dtemissao >= DATE_SUB(CURRENT_DATE, INTERVAL 12 MONTH);
"""
df = pd.read_sql(query, conn)

# Consultar classificações
query_classificacoes = """
SELECT clc_codigo, clc_desc
FROM classificapes;
"""
df_classificacoes = pd.read_sql(query_classificacoes, conn)

# Fechar conexão após carregar os dados
conn.close()

# Criar um dicionário de mapeamento de código para descrição
codigo_to_desc = df_classificacoes.set_index('clc_codigo')['clc_desc'].to_dict()

# Etapa 2: Preparar os dados
df['ped_dtemissao'] = pd.to_datetime(df['ped_dtemissao'])
df['mes_ano'] = df['ped_dtemissao'].dt.to_period('M')

# Agrupar e calcular média mensal de peso por cliente
df_grouped = df.groupby(['ped_pescodigo', 'pes_razao', 'pes_fantasia', 'mes_ano']).agg(total_peso=('ped_pesobruto', 'sum')).reset_index()
df_final = df_grouped.groupby(['ped_pescodigo', 'pes_razao', 'pes_fantasia']).agg(media_peso_mensal=('total_peso', 'mean')).reset_index()

# Segmentar clientes
def segmentar(peso):
    if peso > 599:
        return 'CLIENTE A'
    elif peso >= 400:
        return 'CLIENTE B'
    elif peso >= 200:
        return 'CLIENTE C'
    elif peso >= 80:
        return 'CLIENTE D'
    elif peso > 0:
        return 'CLIENTE E'

# Adicionar segmento baseado na média de peso mensal
df_final['desc_clc_nova'] = df_final['media_peso_mensal'].apply(segmentar)

# Garantir que `df` tenha valores únicos para `ped_pescodigo`
df_unique = df.drop_duplicates(subset='ped_pescodigo')

# Adicionar descrição da classificação atual
df_final['pes_clccodigo'] = df_final['ped_pescodigo'].map(
    df_unique.set_index('ped_pescodigo')['pes_clccodigo']
)
df_final['desc_clc_atual'] = df_final['pes_clccodigo'].map(codigo_to_desc)

# Definir hierarquia explícita
hierarquia = ['CLIENTE E', 'CLIENTE D', 'CLIENTE C', 'CLIENTE B', 'CLIENTE A']

# Identificar mudanças de classificação
def identificar_mudanca(row):
    atual_pos = hierarquia.index(row['desc_clc_atual']) if row['desc_clc_atual'] in hierarquia else -1
    nova_pos = hierarquia.index(row['desc_clc_nova']) if row['desc_clc_nova'] in hierarquia else -1

    if atual_pos == -1 and nova_pos != -1:
        return 'Upgrade'
    elif nova_pos > atual_pos:
        return 'Upgrade'
    elif nova_pos < atual_pos:
        return 'Downgrade'
    else:
        return 'Sem alteração'

df_final['mudanca'] = df_final.apply(identificar_mudanca, axis=1)

# Filtrar apenas clientes com mudanças relevantes
df_mudancas = df_final[df_final['mudanca'] != 'Sem alteração']

# Adicionar a data da atualização
data_atualizacao = datetime.now().strftime('%Y-%m-%d')
df_mudancas['data_atualizacao'] = data_atualizacao

# Adicionar informações da carteira ao relatório
df_mudancas = df_mudancas.merge(
    df[['ped_pescodigo', 'carteira_cliente']].drop_duplicates(),
    on='ped_pescodigo',
    how='left'
)

# Gerar relatório em CSV com a vírgula como separador decimal
df_mudancas[['ped_pescodigo', 'pes_razao', 'pes_fantasia', 'carteira_cliente', 'desc_clc_atual', 'desc_clc_nova', 'media_peso_mensal', 'mudanca', 'data_atualizacao']].to_csv(
    'Relatorio_Alteracoes_Classificacaoxx.csv', index=False, sep=';', decimal=',', encoding='utf-8'
)

# Gerar script SQL para atualizar as classificações
sql_commands = []
for _, row in df_final.iterrows():
    sql = f"UPDATE pessoa SET pes_clccodigo = (SELECT clc_codigo FROM classificapes WHERE clc_desc = '{row['desc_clc_nova']}') WHERE pes_codigo = {row['ped_pescodigo']};"
    sql_commands.append(sql)

with open('atualizar_classificacaoxx.sql', 'w', encoding='utf-8') as file:
    file.write('\n'.join(sql_commands))

print("Relatório em CSV e script SQL gerados com sucesso!")

