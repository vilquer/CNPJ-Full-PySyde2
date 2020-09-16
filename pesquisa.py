# -*- coding: utf-8 -*- --noconsole

import sys
import re
import os
import json
import sqlite3
import subprocess
import pandas as pd
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtWebChannel import QWebChannel
from PySide2.QtWebEngineWidgets import QWebEngineView , QWebEnginePage
from PySide2.QtCore import Qt

from uis.main import Ui_MainWindow

from rede_cnpj import RedeCNPJ
import configs
import config


df = pd.DataFrame()
df_socios = pd.DataFrame()
df_cnae = pd.DataFrame()

######## variáveis com os caminhos relativos
local_url_icone_mapa = QtCore.QUrl.fromLocalFile(os.path.abspath(os.path.join(os.path.dirname(__file__), "resources/rede.PNG")))
local_url_mapa = QtCore.QUrl.fromLocalFile(os.path.abspath(os.path.join(os.path.dirname(__file__), "folder/grafo.html")))
path_output ='folder'

class TableModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]
    
    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Vertical:
                return str(self._data.index[section])

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
	def __init__(self):
		super(MainWindow, self).__init__()
		self.setupUi(self)
		self.edt_cnpj.setFocus()
		self.tabWidget.setCurrentIndex(0)
		self.lbl_nivel.setNum(1)
		self.sld_nivel.setValue(1)



		def muda_nivel():
			#print(str(self.tabWidget.currentIndex()))
			if self.tabWidget.currentIndex() == 3:
				cnpj = ''
				#self.edt_cnpj.setText(cnpj)
				cnpj =re.sub('[^0-9]', '', self.edt_cnpj.text()) 
				if cnpj == '':
					return()
				self.lbl_nivel.setText(str(self.sld_nivel.value()))
				gera_grafico(cnpj, self.sld_nivel.value())
				self.webEngineView.setUrl(QtCore.QUrl(local_url_mapa))
				



		def gera_grafico(cnpj, nivel):
			global local_url_mapa
			self.conn = sqlite3.connect("data\CNPJ_full.db")
			rede = RedeCNPJ(self.conn, nivel_max=nivel, qualificacoes=config.QUALIFICACOES)
			item = cnpj.strip()
			rede.insere_pessoa(1, item.replace('.','').replace('/','').replace('-','').replace(' ','').zfill(14))
			item.replace('.','').replace('/','').replace('-','').replace(' ','').zfill(14)

			with open('viz/template.html', 'r', encoding='utf-8') as template:
				str_html = template.read().replace('<!--GRAFO-->', json.dumps(rede.json()))

			path_html = os.path.join(path_output, 'grafo'+ item +'.html')
			local_url_mapa = QtCore.QUrl.fromLocalFile(os.path.abspath(os.path.join(os.path.dirname(__file__), path_output+'/grafo'+ item +'.html')))
			with open(path_html, 'w', encoding='utf-8') as html:
				html.write(str_html)
			



			#antiga forma de fazer chamada
			#consulta.consulta(tipo_consulta='cnpj', objeto_consulta=cnpj, qualificacoes=config.QUALIFICACOES, path_BD=config.PATH_BD, nivel_max=nivel, path_output='folder', csv=False , colunas_csv=config.COLUNAS_CSV, csv_sep=config.SEP_CSV, graphml=False, gexf=False, viz=True, path_conexoes=None)
			

		def limpar_campos():
			self.edt_cnpj.clear()
			self.lbl_situacao.clear()
			self.edt_razao_social.clear()
			self.edt_matriz.clear()
			self.edt_porte.clear()
			self.edt_nome_fantasia.clear()
			self.edt_data_situacao.clear()
			self.edt_motivo_situacao.clear()
			self.edt_cidade.clear()
			self.edt_pais.clear()
			self.edt_natureza.clear()
			self.edt_dt_ini_atividade.clear()
			self.edt_end_tip_logradouro.clear()
			self.edt_end_logradouro.clear()
			self.edt_end_num.clear()
			self.edt_end_complemento.clear()
			self.edt_end_bairro.clear()
			self.edt_end_cep.clear()
			self.edt_end_uf.clear()
			self.edt_end_municipio.clear()
			self.edt_ddd1.clear()
			self.edt_tel1.clear()
			self.edt_ddd2.clear()
			self.edt_tel2.clear()
			self.edt_ddd3.clear()
			self.edt_tel3.clear()
			self.edt_email.clear()
			self.edt_capital.clear()
			self.edt_simples.clear()
			self.edt_dt_op_simples.clear()
			self.edt_dt_ex_simples.clear()
			self.edt_mei.clear()
			self.edt_especial.clear()
			self.edt_dt_especial.clear()
			self.edt_cnpj.setFocus()
			self.webEngineView.setUrl(QtCore.QUrl(local_url_icone_mapa))
			self.lbl_situacao.setStyleSheet("")
			self.lbl_nivel.setNum(1)
			self.sld_nivel.setValue(1)

			df = pd.DataFrame([''])
			
			self.model = TableModel(df)
			self.table_socios.setModel(self.model)
			self.table_cnae.setModel(self.model)
			self.edt_cnae.clear()

			self.tabWidget.setCurrentIndex(0)
			self.edt_cnpj.setFocus()
			

		def pesquisa():
			################### Criar validador do cnpj ###################
			cnpj = ''
			cnpj =re.sub('[^0-9]', '', self.edt_cnpj.text()) 

			######## conexão com o DB ########
			### Empresas
			self.conn = sqlite3.connect("data\CNPJ_full.db")
			sql = (f"select * from empresas where cnpj = '{cnpj}'")
			#print(sql)
			df = pd.read_sql_query(sql, self.conn)
			### Sócios
			sql = (f"select tipo_socio as Tipo, nome_socio as Nome, cnpj_cpf_socio as 'CPF-CNPJ', cod_qualificacao as 'Classificação', perc_capital as 'Perc. do Capital', data_entrada as 'Data de Entrada', nome_pais_ext as 'País', cpf_repres as 'CPF Representante', nome_repres as 'Nome Representante', cod_qualif_repres as 'Qualificação Representante' from socios where cnpj =  '{cnpj}'")
			#print(sql)
			df_socios = pd.read_sql_query(sql, self.conn)
			### CNAEs
			sql = (f"SELECT cnae as CNAE FROM cnaes_secundarios WHERE cnpj = '{cnpj}'")
			df_cnae = pd.read_sql_query(sql, self.conn)
			self.conn.close()

			if cnpj == '' or len(df) != 1:
					return()

			
			#Trocando os códigos pelas descrições que estão no arquivo config.py
			df['matriz_filial'] = df['matriz_filial'].map(configs.dict_matriz_filial)
			df['situacao'] = df['situacao'].map(configs.dict_situacao)
			df['motivo_situacao'] = df['motivo_situacao'].map(configs.dict_motivo_situacao)
			df['cod_nat_juridica'] = df['cod_nat_juridica'].map(configs.dict_nat_juridica)
			df['cnae_fiscal'] = df['cnae_fiscal'].map(configs.dict_cnaes)
			df['qualif_resp'] = df['qualif_resp'].map(configs.dict_qualif)
			df['porte'] = df['porte'].map(configs.dict_porte)
			df['opc_simples'] = df['opc_simples'].map(configs.dict_opc_simples)
			df['opc_mei'] = df['opc_mei'].map(configs.dict_opc_mei)
			#df_socios
			df_socios['Tipo'] = df_socios['Tipo'].map(configs.dict_tipo_socio)
			df_socios['Classificação'] = df_socios['Classificação'].map(configs.dict_qualif)
			df_socios['Qualificação Representante'] = df_socios['Qualificação Representante'].map(configs.dict_qualif)
			#df_CNAEs
			df_cnae['CNAE'] = df_cnae['CNAE'].map(configs.dict_cnaes)


			######## Convertendo as datas ########
			df['data_situacao'] = pd.to_datetime(df.data_situacao)
			df['data_situacao'] = df['data_situacao'].dt.strftime('%d/%m/%Y')
			df['data_inicio_ativ'] = pd.to_datetime(df.data_inicio_ativ)
			df['data_inicio_ativ'] = df['data_inicio_ativ'].dt.strftime('%d/%m/%Y')
			df['data_opc_simples'] = pd.to_datetime(df.data_opc_simples)
			df['data_opc_simples'] = df['data_opc_simples'].dt.strftime('%d/%m/%Y')
			df['data_exc_simples'] = pd.to_datetime(df.data_exc_simples)
			df['data_exc_simples'] = df['data_exc_simples'].dt.strftime('%d/%m/%Y')
			df['data_sit_especial'] = pd.to_datetime(df.data_sit_especial)
			df['data_sit_especial'] = df['data_sit_especial'].dt.strftime('%d/%m/%Y')
			#df_socios
			df_socios['Data de Entrada'] = pd.to_datetime(df_socios['Data de Entrada'])
			df_socios['Data de Entrada'] = df_socios['Data de Entrada'].dt.strftime('%d/%m/%Y')
			

			### limpando os NaN
			df.fillna(' ', inplace=True)
			df_socios.fillna('', inplace=True)
			df_cnae.fillna('não encontrado', inplace=True)

			######## Povoando a tela  Tab Geral ########
			self.lbl_situacao.setText(df['situacao'][0])
			self.lbl_situacao.setStyleSheet("") if  df['situacao'][0] == "ATIVA" else self.lbl_situacao.setStyleSheet("QLabel { background-color : red; color : black; }")
			self.edt_razao_social.setText(df['razao_social'][0])
			self.edt_matriz.setText(df['matriz_filial'][0])
			self.edt_porte.setText(df['porte'][0])
			self.edt_nome_fantasia.setText(df['nome_fantasia'][0])
			self.edt_data_situacao.setText(str(df['data_situacao'][0]))
			self.edt_motivo_situacao.setText(df['motivo_situacao'][0])
			self.edt_cidade.setText(df['nm_cidade_exterior'][0])
			self.edt_pais.setText(df['nome_pais'][0])
			self.edt_natureza.setText(df['cod_nat_juridica'][0])
			self.edt_dt_ini_atividade.setText(str(df['data_inicio_ativ'][0]))
			self.edt_end_tip_logradouro.setText(df['tipo_logradouro'][0])
			self.edt_end_logradouro.setText(df['logradouro'][0])
			self.edt_end_num.setText(df['numero'][0])
			self.edt_end_complemento.setText(df['complemento'][0])
			self.edt_end_bairro.setText(df['bairro'][0])
			self.edt_end_cep.setText(df['cep'][0])
			self.edt_end_uf.setText(df['uf'][0])
			self.edt_end_municipio.setText(df['municipio'][0])
			self.edt_ddd1.setText(df['ddd_1'][0])
			self.edt_tel1.setText(df['telefone_1'][0])
			self.edt_ddd2.setText(df['ddd_2'][0])
			self.edt_tel2.setText(df['telefone_2'][0])
			self.edt_ddd3.setText(df['ddd_fax'][0])
			self.edt_tel3.setText(df['num_fax'][0])
			self.edt_email.setText(df['email'][0])
			self.edt_capital.setText(str(df['capital_social'][0]).replace(".", ","))
			self.edt_simples.setText(df['opc_simples'][0])
			self.edt_dt_op_simples.setText(str(df['data_opc_simples'][0]))
			self.edt_dt_ex_simples.setText(str(df['data_exc_simples'][0]))
			self.edt_mei.setText(df['opc_mei'][0])
			self.edt_especial.setText(df['sit_especial'][0])
			self.edt_dt_especial.setText(str(df['data_sit_especial'][0]))

			
			### Carregando os sócios na tabela da Tab Sócios
			self.model = TableModel(df_socios)
			self.table_socios.setModel(self.model)


			### Carregando os CNAEs na tabela da Tab CNAE
			self.edt_cnae.setText(df['cnae_fiscal'][0])
			self.model = TableModel(df_cnae)
			self.table_cnae.setModel(self.model)

			df = pd.DataFrame([''])

			self.tabWidget.setCurrentIndex(0)

		def abrir_navegador():
			subprocess.Popen('C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'+ ' ' + local_url_mapa.toString())
	
			
		######## Eventos ########
		self.btn_pesquisar.clicked.connect(pesquisa)
		self.btn_limpar.clicked.connect(limpar_campos)
		self.sld_nivel.valueChanged.connect(muda_nivel)
		self.tabWidget.currentChanged.connect(muda_nivel)
		self.commandLinkButton.clicked.connect(abrir_navegador)

		
		

if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	window = MainWindow()
	window.show()
	sys.exit(app.exec_())