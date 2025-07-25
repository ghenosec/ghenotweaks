# Gheno Tweaks

Uma ferramenta simples em Python para aplicar otimizações de desempenho e jogos no Windows com um clique.
Criei com o intuito de, após o computador formatado, em poucos segundos terá seu pc pré otimizado.

<p align="center">
 <img src="https://github.com/ghenosec/ghenotweaks/blob/main/giftweak.gif" alt="Logo" height=400></a>
</p>

## Funcionalidades

- Criação de Ponto de Restauração do Sistema
- Adiciona e ativa o plano de energia "Desempenho Máximo"
- Otimiza configurações da NVIDIA para desempenho (automático)
- Otimiza o Modo de Jogo e desativa a Xbox Game Bar
- Reduz o input lag do teclado e mouse via edições de registro
- Desativa aplicativos rodando em segundo plano

---

## Como Usar

1.  Vá para a [**página de Releases**](https://github.com/ghenosec/GhenoTweaks/releases) do projeto.
2.  Na seção "Assets" do lançamento mais recente, baixe o arquivo `Gheno Tweaks.exe`.
3.  Execute o arquivo. O Windows pedirá permissão de Administrador, o que é necessário para que as otimizações funcionem.

**AVISO:** Este programa modifica o Registro do Windows. Use por sua conta e risco. É altamente recomendado usar a função "Criar Ponto de Restauração" antes de aplicar outras otimizações.

---

## Como Compilar a Partir do Código-Fonte

Se preferir compilar o executável você mesmo:

1.  Instale o Python.
2.  Clone este repositório.
3.  Instale as dependências:
    ```bash
    pip install pyinstaller
    ```
4.  Execute o comando para compilar:
    ```bash
    pyinstaller --onefile --windowed --name "Gheno Tweaks" --icon="icone.ico" optimizer.py
    ```
5.  O executável estará na pasta `dist/`.
