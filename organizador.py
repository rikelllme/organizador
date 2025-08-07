import os
import shutil
<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Matriz de Releases (3 Semanas)</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Inter', sans-serif; }
    .font-mono { font-family: 'Roboto Mono', monospace; }
    .custom-scrollbar::-webkit-scrollbar { height: 8px; }
    .custom-scrollbar::-webkit-scrollbar-track { background-color: #1f2937; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background-color: #4b5563; border-radius: 10px; }
  </style>
</head>
<body class="bg-gray-900 text-gray-200 antialiased">
  <div class="container mx-auto p-4 sm:p-6 lg:p-8">

    <!-- Cabeçalho -->
    <div class="text-center mb-6">
      <h1 class="text-2xl sm:text-3xl font-bold text-white">📊 Matriz de Releases - BB x LA</h1>
      <p id="week-range" class="text-lg text-cyan-400 font-semibold"></p>
    </div>

    <!-- Tabela -->
    <div class="overflow-x-auto bg-gray-800 rounded-xl shadow-2xl custom-scrollbar">
      <table class="min-w-full text-sm text-center">
        <thead class="bg-gray-700/50 sticky top-0 z-10">
          <tr>
            <th rowspan="2" class="p-3 tracking-wider border-r border-b border-gray-600">Market Name</th>
            <th rowspan="2" class="p-3 tracking-wider border-r border-b border-gray-600">Model / Type</th>
            <th id="week-head-1" colspan="7" class="p-3 tracking-wider border-r border-b border-gray-600"></th>
            <th id="week-head-2" colspan="7" class="p-3 tracking-wider border-r border-b border-gray-600"></th>
            <th id="week-head-3" colspan="7" class="p-3 tracking-wider border-b border-gray-600"></th>
          </tr>
          <tr>
            ${["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"].map(d => `<th class="p-2 font-medium text-gray-400 border-r border-gray-600">${d}</th>`).join('')}
            ${["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"].map(d => `<th class="p-2 font-medium text-gray-400 border-r border-gray-600">${d}</th>`).join('')}
            ${["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"].map((d, i) => `<th class="p-2 font-medium text-gray-400${i < 6 ? ' border-r border-gray-600' : ''}">${d}</th>`).join('')}
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-700">

          <!-- Exemplo genérico -->
          <tr class="bg-gray-800">
            <td rowspan="2" class="p-3 font-bold border-r border-gray-700 align-middle">Dispositivo Genérico</td>
            <td class="p-3 font-mono text-left border-r border-gray-700">
              <span class="bg-blue-600/80 text-white font-bold text-xs px-2 py-1 rounded-full mr-2">BB</span>modeloteste
            </td>
            ${Array(21).fill('<td></td>').join('')}
          </tr>
          <tr class="bg-gray-800">
            <td class="p-3 font-mono text-left border-r border-gray-700">
              <span class="bg-green-600/80 text-white font-bold text-xs px-2 py-1 rounded-full mr-2">LA</span>modeloteste
            </td>
            ${Array(21).fill('<td></td>').join('')}
          </tr>

        </tbody>
      </table>
    </div>

    <footer class="mt-8 text-center text-gray-500 text-sm">
      <p>Design atualizado por Gemini</p>
    </footer>
  </div>

  <script>
    document.addEventListener('DOMContentLoaded', () => {
      function getWeekNumber(d) {
        d = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
        d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
        const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
        const weekNo = Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
        return weekNo;
      }

      const now = new Date();
      const w1 = getWeekNumber(now);
      const w2 = w1 + 1;
      const w3 = w1 + 2;

      document.getElementById('week-head-1').textContent = `Semana ${w1}`;
      document.getElementById('week-head-2').textContent = `Semana ${w2}`;
      document.getElementById('week-head-3').textContent = `Semana ${w3}`;
      document.getElementById('week-range').textContent = `(W${w1} a W${w3})`;
    });
  </script>
</body>
</html>

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

