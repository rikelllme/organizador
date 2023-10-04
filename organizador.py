import os
import shutil


diretorio_atestados = "C:\\Users\\Rikellme\\Desktop\\Atestado Virtual"
diretorio_colaboradores = "C:\\Users\\Rikellme\\Desktop\\Atestado Virtual\\Colaboradores"


if not os.path.exists(diretorio_atestados):
    print(f"Diretório de origem '{diretorio_atestados}' não existe.")
else:
   
    arquivos_atestados = os.listdir(diretorio_atestados)

    
    for arquivo in arquivos_atestados:
       
        matricula = arquivo[:8]

        
        pasta_colaborador = os.path.join(diretorio_colaboradores, matricula)

       
        if not os.path.exists(pasta_colaborador):
            os.makedirs(pasta_colaborador)
       
        caminho_origem = os.path.join(diretorio_atestados, arquivo)
        if os.path.exists(caminho_origem):
           
            caminho_destino = os.path.join(pasta_colaborador, arquivo)
            contador = 1
            while os.path.exists(caminho_destino):
                          
                nome_base, extensao = os.path.splitext(arquivo)
                arquivo = f"{nome_base}_{contador}{extensao}"
                caminho_destino = os.path.join(pasta_colaborador, arquivo)
                contador += 1

            try:
                shutil.move(caminho_origem, caminho_destino)
                print(f"Arquivo '{arquivo}' movido com sucesso para '{pasta_colaborador}'.")
            except Exception as e:
                print(f"Erro ao mover o arquivo '{arquivo}': {str(e)}")
        else:
            print(f"Arquivo '{arquivo}' não encontrado em '{diretorio_atestados}'.")
