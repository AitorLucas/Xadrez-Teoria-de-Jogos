import chess
import random
import time
import os
import statistics
from colorama import Fore, Style, init
import threading

init(autoreset=True)

transposition_table = {}
move_history = []
best_move = None
search_completed = False

# Verifica se um movimento é legal no tabuleiro atual
def is_legal_move(board, move):
    try:
        move_obj = chess.Move.from_uci(move)
        return move_obj in board.legal_moves
    except Exception:
        return False

# Imprime o tabuleiro de xadrez com rótulos e cores para facilitar a visualização
def print_board_with_labels(board, system_color):
    # os.system('cls')  # Limpa o terminal no Windows
    board_str = str(board)
    rows = board_str.split("\n")
    labeled_rows = []
    
    for i, row in enumerate(rows):
        colored_row = ""
        for char in row:
            if char.isalpha():
                # Colore as peças do sistema de verde e as do adversário de vermelho
                if (char.isupper() and system_color == chess.WHITE) or (char.islower() and system_color == chess.BLACK):
                    colored_row += f"{Fore.GREEN}{Style.BRIGHT}{char.upper()}{Style.RESET_ALL}"
                else:
                    colored_row += f"{Fore.RED}{Style.BRIGHT}{char.upper()}{Style.RESET_ALL}"
            else:
                colored_row += char
        labeled_rows.append(f"{8 - i} {colored_row}")
    
    labeled_board = "\n".join(labeled_rows)
    
    top_label = f"{Fore.RED}{Style.BRIGHT}Adversário{Style.RESET_ALL}"
    bottom_label = f"{Fore.GREEN}{Style.BRIGHT}Sistema{Style.RESET_ALL}"
    
    if system_color == chess.BLACK:
        top_label, bottom_label = bottom_label, top_label
    
    labeled_board = f"{top_label}\n  a b c d e f g h\n" + labeled_board + f"\n  a b c d e f g h\n{bottom_label}"
    
    print(labeled_board)

# Função que define a prioridade de um movimento
# Args:
#     board (chess.Board): O tabuleiro de xadrez atual.
#     move (chess.Move): O movimento a ser avaliado.
# Returns:
#     int: A prioridade do movimento.
def move_priority(board, move):
    if board.is_capture(move):
        return 3  # Capturas têm a maior prioridade
    if board.piece_at(move.from_square).piece_type == chess.PAWN and (chess.square_rank(move.to_square) == 0 or chess.square_rank(move.to_square) == 7):
        return 2  # Promoções de peões têm a segunda maior prioridade
    if board.gives_check(move):
        return 1  # Movimentos que dão cheque têm a terceira maior prioridade
    if board.is_check():
        return 4  # Movimentos que tiram o rei de cheque têm a maior prioridade
    return 0  # Outros movimentos têm a menor prioridade

# Ordena os movimentos legais com base em uma heurística simples que prioriza capturas, promoções de peões e proteção do rei
# Args:
#     board (chess.Board): O tabuleiro de xadrez atual.
# Returns:
#     list: Lista de movimentos legais ordenados.
def order_moves(board):
    return sorted(board.legal_moves, key=lambda move: move_priority(board, move), reverse=True)

# Implementa a busca alfa-beta para encontrar o melhor movimento
# Args:
#     board (chess.Board): O tabuleiro de xadrez atual.
#     depth (int): A profundidade máxima da busca.
#     alpha (float): O valor alfa para poda alfa-beta.
#     beta (float): O valor beta para poda alfa-beta.
#     maximizing_player (bool): True se o jogador atual é o jogador maximizador, False caso contrário.
#     captured_pieces (dict): Dicionário de peças capturadas para ambos os jogadores.
# Returns:
#     float: A avaliação do tabuleiro.
def alpha_beta_search(board, depth, alpha, beta, maximizing_player, captured_pieces):
    global best_move, search_completed
    board_fen = board.fen()
    
    # Verifica se a posição já foi avaliada anteriormente
    if board_fen in transposition_table:
        return transposition_table[board_fen]
    
    # Condição de parada: profundidade zero ou fim do jogo
    if depth == 0 or board.is_game_over():
        return evaluate_board(board, captured_pieces)
    
    if maximizing_player:
        max_eval = float('-inf') # Valor de alfa
        for move in order_moves(board): # Ordena os movimentos para melhorar a eficiência da busca
            captured_piece = board.piece_at(move.to_square) # Captura a peça adversária se houver
            if captured_piece: # Adiciona a peça capturada à lista de peças capturadas
                captured_pieces[maximizing_player].append(captured_piece) 
            
            board.push(move) # Realiza o movimento
            move_history.append(board.fen()) # Adiciona a posição do tabuleiro ao histórico de movimentos
            eval = alpha_beta_search(board, depth - 1, alpha, beta, False, captured_pieces) # Chama a função recursivamente

            board.pop() # Desfaz o movimento
            move_history.pop() # Remove a posição do tabuleiro do histórico de movimentos
            
            if captured_piece: # Remove a peça capturada da lista de peças capturadas
                captured_pieces[maximizing_player].pop()
            
            if eval > max_eval: # Atualiza a melhor avaliação
                max_eval = eval 
                if depth == 7:  # Atualiza o melhor movimento no nível raiz
                    best_move = move

            alpha = max(alpha, eval)  # Atualiza o valor de alfa
            if beta <= alpha: # Poda beta
                break

        transposition_table[board_fen] = max_eval # Adiciona a avaliação ao cache da tabela de transposição
        return max_eval
    
    else:
        min_eval = float('inf') # Valor de beta
        for move in order_moves(board): # Ordena os movimentos para melhorar a eficiência da busca
            captured_piece = board.piece_at(move.to_square) # Captura a peça adversária se houver
            if captured_piece: # Adiciona a peça capturada à lista de peças capturadas
                captured_pieces[maximizing_player].append(captured_piece)

            board.push(move) # Realiza o movimento
            move_history.append(board.fen()) # Adiciona a posição do tabuleiro ao histórico de movimentos
            eval = alpha_beta_search(board, depth - 1, alpha, beta, True, captured_pieces) # Chama a função recursivamente

            board.pop() # Desfaz o movimento
            move_history.pop() # Remove a posição do tabuleiro do histórico de movimentos
            
            if captured_piece: # Remove a peça capturada da lista de peças capturadas
                captured_pieces[maximizing_player].pop()
            
            min_eval = min(min_eval, eval) # Atualiza a melhor avaliação
            beta = min(beta, eval) # Atualiza o valor de beta
            
            if beta <= alpha: # Poda alfa
                break

        transposition_table[board_fen] = min_eval # Adiciona a avaliação ao cache da tabela de transposição
        return min_eval

# Avalia o tabuleiro de xadrez atual
def evaluate_board(board, captured_pieces):
    board_value = sum(piece_value(piece) for piece in board.piece_map().values()) # Valor das peças no tabuleiro
    captured_value = sum(piece_value(piece) for piece in captured_pieces[True]) - sum(piece_value(piece) for piece in captured_pieces[False]) # Valor das peças capturadas
    repetition_penalty = -10 if move_history.count(board.fen()) > 1 else 0 # Penalidade por repetição de posição
    return board_value + captured_value + repetition_penalty #  Avaliação final

# Retorna o valor de uma peça de xadrez
# Args:
#     piece (chess.Piece): A peça de xadrez.
# Returns:
#     int: O valor da peça.
def piece_value(piece):
    values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }
    return values[piece.piece_type] if piece.color == chess.WHITE else -values[piece.piece_type]

# Inicia a busca pelo melhor movimento usando a busca alfa-beta.
# Args:
#     board (chess.Board): O tabuleiro de xadrez atual.
#     captured_pieces (dict): Dicionário de peças capturadas para ambos os jogadores.
def search_best_move(board, captured_pieces):
    global search_completed
    search_completed = False
    alpha_beta_search(board, 7, float('-inf'), float('inf'), True, captured_pieces)
    search_completed = True

# Função principal que controla o fluxo do jogo de xadrez.
def main():
    global best_move
    board = chess.Board()
    
    system_times = []
    system_moves = []
    opponent_moves = []
    captured_pieces = {True: [], False: []}  # True para o sistema, False para o adversário
    
    is_system_turn = random.choice([True, False])
    system_color = chess.WHITE if is_system_turn else chess.BLACK
    
    print_board_with_labels(board, system_color)
    
    while not board.is_game_over():
        if is_system_turn:
            print("<VEZ DO SISTEMA>")
            start_time = time.time()
            best_move = random.choice(list(board.legal_moves))  # Inicializa com um movimento legal aleatório
            search_thread = threading.Thread(target=search_best_move, args=(board, captured_pieces)) # Inicia a busca em uma thread
            search_thread.start()
            search_thread.join(timeout=120)  # Limita o tempo de execução da busca a 120 segundos
            
            if not search_completed:
                print("Tempo excedido! Usando o melhor movimento encontrado até agora.")
            
            elapsed_time = time.time() - start_time
            system_times.append(elapsed_time)
            print(f"Tempo de execução: {elapsed_time:.2f}s")
            
            if best_move is None or not is_legal_move(board, best_move.uci()):
                print(f"Movimento {best_move} ilegal sugerido pelo sistema! Tentando novamente.")
                continue
            
            board.push(best_move) # Realiza o movimento
            system_moves.append(best_move.uci()) # Adiciona o movimento ao histórico de movimentos
            
            print("Movimento do sistema:", best_move)
            print_board_with_labels(board, system_color)
            is_system_turn = False
        else:
            print("<VEZ DO ADVERSÁRIO>")
            move = input("Digite o movimento do adversário: ")
            
            if not is_legal_move(board, move):
                print(f"Movimento {move} ilegal! Tente novamente.")
                continue
            
            captured_piece = board.piece_at(chess.Move.from_uci(move).to_square) # Captura a peça do sistema se houver
            if captured_piece: # Adiciona a peça capturada à lista de peças capturadas
                captured_pieces[False].append(captured_piece)
            
            board.push(chess.Move.from_uci(move)) # Realiza o movimento
            opponent_moves.append(move) # Adiciona o movimento ao histórico de movimentos
            
            print_board_with_labels(board, system_color)
            is_system_turn = True
    
    if system_times:
        avg_time = statistics.mean(system_times)
        std_dev_time = statistics.stdev(system_times)
        print(f"\nMédia de tempo das jogadas do sistema: {avg_time:.2f}s")
        print(f"Desvio padrão do tempo das jogadas do sistema: {std_dev_time:.2f}s")
        
        with open("game_data.txt", "w") as file:
            file.write(f"Média de tempo das jogadas do sistema: {avg_time:.2f}s\n")
            file.write(f"Desvio padrão do tempo das jogadas do sistema: {std_dev_time:.2f}s\n")
            file.write("\nMovimentos do sistema:\n")
            file.write("\n".join(system_moves))
            file.write("\n\nMovimentos do adversário:\n")
            file.write("\n".join(opponent_moves))

if __name__ == "__main__":
    main()