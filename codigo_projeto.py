import socket as s
from datetime import datetime
import threading


jogada_eu = ""
jogada_oponente = ""

def comparar_resultado():
    global jogada_oponente, jogada_eu

    # Se os dois já fizeram suas jogadas
    if jogada_oponente != "" and jogada_eu != "":
        if jogada_eu == jogada_oponente:
            print("EMPATE")
        elif jogada_eu == "3" and jogada_oponente == "1": # 1 é Papel, Tesoura vence de Papel
            print("VOCÊ GANHOU")
        elif jogada_eu == "1" and jogada_oponente == "2": # 2 é Pedra, Papel vence de Pedra
            print("VOCÊ GANHOU")
        elif jogada_eu == "2" and jogada_oponente == "3": # 3 é Tesoura, Pedra vence de Tesoura
            print("VOCÊ GANHOU")
        else: # Se sua jogada não ganhou
            print("VOCÊ PERDEU")
        print("=" *27)

        # Limpa as jogadas para o próximo round
        jogada_eu = ""
        jogada_oponente = ""
    
    
def receber_dados(conexao:s.socket):
    global jogada_oponente

    while True:
        mensagem = ""

        try:
            # 1024 é a quantidade que um buffer vai ter e será a mensagem que o cliente enviar.
            # Aqui o outro dispositivo está esperando o outro jogador mandar alguma coisa.
            dados = conexao.recv(1024)

            if not dados:
                print("A conexão foi finalizada pelo outro jogador...")
                break
            # Aqui ele vai decodificar o que recebeu, não foi colocado na mesma linha para não dá um erro ao converter diretamente. Também fica mais fácil de capturar erros específicos.
            mensagem = dados.decode(errors="strict")
        except Exception as e:
            # O padrão de comunicação é unicode-8, se for um diferente pode dá erro.
            print("Conexão perdida ou erro ao receber os dados")
            salvar_erro(str(e))
            break

        if mensagem == "sair":
            print("O outro jogador encerrou a conexão...")
            print("Encerrando a conexão...")
            conexao.close()
            break

        if foi_uma_jogada(mensagem):
            jogada_oponente = mensagem
            # Quando salvar no chat, ele não vai salvar só como 1, ele vai salvar como Papel
            salvar_mensagem_chat(f"Jogada Recebida: {traduzir_a_jogada(mensagem)}")
            if jogada_eu == "":
                print("O outro jogador já fez sua jogada... faça a sua:")
                print("1. Papel, 2. Pedra, 3. Tesoura. ou sair")
            else:
                comparar_resultado()
        else:
            print("Chat: ", mensagem)
            salvar_mensagem_chat(f"Chat recebido: {mensagem}")

# Como ambos vão funcionar como cliente e servidor ao mesmo tempo, não precisamos repetir esse código para cada função, só reutilizar
def comecar_jogo(conexao: s.socket):    
    global jogada_eu

    # Passamos a função 'receber_dados' como o alvo, e a tupla 'args'       
    processamento_paralelo = threading.Thread(target=receber_dados, args=(conexao,))
    # Fazer o progrma fechar mesmo com uma thread
    processamento_paralelo.daemon = True        
    processamento_paralelo.start()

    print("Digite uma das opções: \n1. Papel, 2. Pedra, 3. Tesoura, sair. \n")
    
    while True:
        print("=" * 27)
        # Inicia um processo em paralelo para ficar recebendo dados.
        mensagem = input().strip()

        if mensagem == "sair" or jogada_oponente == "sair":
            try:    
                # Se ele escolher sair, o programa vai enviar uma mensagem padrão para finalizar o jogo.
                conexao.send("sair".encode())
            except Exception as e:
                print("Ocorreu um erro ao enviar a mensagem.")
                salvar_erro(str(e))
            # Finaliza a conexão do servidor.
            conexao.close()
            print("Conexão finalizada.")
            break

        if foi_uma_jogada(mensagem):
            if jogada_eu != "":
                print("Você já jogou espere seu oponente.")
                continue

            jogada_eu = mensagem
            salvar_mensagem_chat("Enviada a Jogada: " + mensagem)
        
            try:
                conexao.send(mensagem.encode())
                print("Jogada realizada! Espere seu oponente...")
            except Exception as e:
                print("Ocorreu um erro ao enviar a mensagem.")
                salvar_erro(str(e))
            comparar_resultado()
            continue
        else:
            salvar_mensagem_chat("Enviado Chat: "+ mensagem)
            try:
                conexao.send(mensagem.encode())
            except Exception as e:
                print("Ocorreu um erro ao enviar a mensagem.")
                salvar_erro(str(e))
            continue

    
def foi_uma_jogada(texto: str) -> bool:
    return (texto == "1" or texto == "2" or texto == "3")

def traduzir_a_jogada(jogada:str) -> str:
    if not jogada.isdigit():
        return "Jogada desconhecida"
    jogada = int(jogada)
    match jogada:
        case 1:
            return "Papel"
        case 2:
            return "Pedra"
        case 3:
            return "Tesoura"
        case _:
            return "Jogada desconhecida"

def salvar_mensagem_chat(mensagem:str):
    # Toda vez que uma mensagem foi recebida ou enviada ele vai existrar 
    with open("chat.log", "a") as arquivo:
        horario = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        arquivo.write(f"{horario}: {mensagem}\n")

def salvar_erro(erro:str):
    with open("erros.log", "a") as arquivo:
        horario = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        arquivo.write(f"Um erro acontece no {horario}: {erro}\n")


conexao = int(input("Você vai ser: \n1. Servidor (P1) \n2. Cliente (P2) \n"))
# Todo socket vai ter uma porta, vamos usar uma porta padrão no programa para não repetir, mas o programa poderia pedir uma porta especfica, assim esse programa poderia rodar na mesma rede com outros computadores.
# A porta poderia ser qualquer número desde que seja acima de 1023 e até 65535, por exemplo.
porta_padrao = 7777
# porta_padrao = int(input("Insira o número da porta"))

# Caso a conexão seja servidor
if conexao == 1:
    # AF_INET esse é o identificador para endereços IPV4.
    # SOCK_STREAM é utilizado para utilizar o protocolo TCP.
    servidor = s.socket(s.AF_INET, s.SOCK_STREAM)
    # "localhost" esse vai ser o IP que vai usado para o servidor. Ele vai utilizar o ip localmente.
    # Poderia ser qualquer número desde que seja acima de 1023 e até 65535.
    try:
        servidor.bind(("0.0.0.0", porta_padrao))
        # Esse listen vai servir para falar quantas conexões o servidor vai deseja ouvir, como são só dois jogadores pode ser só uma conexão.
        servidor.listen(1)
        hostname = s.gethostname()
        ip_local = s.gethostbyname(hostname)
        # precisamos ver se o cliente aceitou a solicitação.
        print("=" * 27)
        print(f"Seu ip é provavelmente: {ip_local}")
        print(f"Peça para alguém se conectar no ip acima, porta: {porta_padrao}...")
        # Estabele a conexão
        connection, address = servidor.accept()
        # Essa porta é uma porta que o nosso servidor encontrar para enviar os dados durante o tempo de execução do programa.
        print(f"Conexão realizado no endereço: {address}")
        # Depois da conexão inicia o jogo.
        comecar_jogo(connection)
    except Exception as e:
        print(f"Algum erro aconteceu ao tentar iniciar o servidor,", e)
        salvar_erro(str(e))        

# Caso a conexão seja um cliente
elif conexao == 2:
    conexao_ip_outro= input("Digite o ip do servidor (ou digite nada para se conectar à rede local): ").strip()
    if conexao_ip_outro == "":
        conexao_ip_outro = "localhost"
    # O AF_INET serve para ser o endereço sendo IPV4
    # SOCK_STREAM é o protocolo que será usado, esse é usado para a conexão TCP, que é orientado à conexão
    cliente = s.socket(s.AF_INET, s.SOCK_STREAM)
    # Aqui o cliente vai se conectar com aquela porta/endereço.
    try:
        cliente.connect((conexao_ip_outro, porta_padrao))
        print("Conectado ao servidor!")
        # Depois da conexão inicia o jogo.
        comecar_jogo(cliente)
    except Exception as e:
        print(f"Não foi possível conectar a {conexao_ip_outro}:{porta_padrao}")
        print("Verifique se o ip está correto e se o servidor já foi iniciado.")
        salvar_erro(str(e))
else:
    print("Digite uma opção válida")

print("Programa encerrado")

