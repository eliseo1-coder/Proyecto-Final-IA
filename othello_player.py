import requests
import random
import sys
import time
import threading

### Dirección del servidor público
### Servidor de pruebas
host_name = 'http://ec2-18-188-26-92.us-east-2.compute.amazonaws.com:8000'

class OthelloClient:

    def __init__(self, username):
        ### Nombre de usuario del jugador
        self.username = username
        ### Símbolo del jugador en una partida (1 para blanco, -1 para negro)
        self.current_symbol = 0

    def connect(self, session_name) -> bool:
        """
        Conectar a la sesión del juego.
        
        :param session_name: Nombre de la sesión del juego a la que se quiere unir
        :return: True si la conexión fue exitosa, False en caso contrario
        """
        new_player = requests.post(host_name + '/player/new_player?session_name=' + session_name + '&player_name=' + self.username)
        new_player = new_player.json()
        self.session_name = session_name
        print(new_player['message'])
        return new_player['status'] == 200

    def play(self):
        """
        Bucle principal del juego. Verifica continuamente el estado del juego y realiza movimientos cuando es el turno del jugador.
        """
        session_info = requests.post(host_name + '/game/game_info?session_name=' + self.session_name)
        session_info = session_info.json()

        while session_info['session_status'] == 'active':
            try:
                if session_info['round_status'] == 'ready':

                    match_info = requests.post(host_name + '/player/match_info?session_name=' + self.session_name + '&player_name=' + self.username)
                    match_info = match_info.json()

                    while match_info['match_status'] == 'bench':
                        print('Estás en la banca esta ronda. Descansa mientras esperas.')
                        time.sleep(15)
                        match_info = requests.post(host_name + '/player/match_info?session_name=' + self.session_name + '&player_name=' + self.username)
                        match_info = match_info.json()

                    if match_info['match_status'] == 'active':
                        self.current_symbol = match_info['symbol']
                        if self.current_symbol == 1:
                            print('¡Vamos a jugar! Eres las piezas blancas.')
                        if self.current_symbol == -1:
                            print('¡Vamos a jugar! Eres las piezas negras.')

                    while match_info['match_status'] == 'active':
                        turn_info = requests.post(host_name + '/player/turn_to_move?session_name=' + self.session_name + '&player_name=' + self.username + '&match_id=' + match_info['match'])
                        turn_info = turn_info.json()
                        while not turn_info['game_over']:
                            if turn_info['turn']:
                                print('PUNTUACIÓN ', turn_info['score'])
                                row, col = self.AI_MOVE(turn_info['board'])
                                move = requests.post(
                                    host_name + '/player/move?session_name=' + self.session_name + '&player_name=' + self.username + '&match_id=' +
                                    match_info['match'] + '&row=' + str(row) + '&col=' + str(col))
                                move = move.json()
                                print(move['message'])
                            turn_info = requests.post(host_name + '/player/turn_to_move?session_name=' + self.session_name + '&player_name=' + self.username + '&match_id=' + match_info['match'])
                            turn_info = turn_info.json()

                        print('Juego terminado. Ganador: ' + turn_info['winner'])
                        match_info = requests.post(host_name + '/player/match_info?session_name=' + self.session_name + '&player_name=' + self.username)
                        match_info = match_info.json()
                else:
                    print('Esperando el sorteo del partido...')
                    time.sleep(5)

            except requests.exceptions.ConnectionError:
                continue

            session_info = requests.post(host_name + '/game/game_info?session_name=' + self.session_name)
            session_info = session_info.json()

    def AI_MOVE(self, board):
        """
        Determina el mejor movimiento a realizar basado en el estado del tablero.
        
        :param board: El estado actual del tablero
        :return: Una tupla (fila, columna) que representa el mejor movimiento
        """
        # Usar un algoritmo simple al inicio del juego y cambiar a minimax en la etapa final
        num_empty = sum(row.count(0) for row in board)
        if num_empty > 20:  # Usar heurística simple en las primeras etapas del juego
            return self.simple_heuristic_move(board)
        else:  # Usar minimax en la etapa final del juego
            return self.minimax_with_time_limit(board, self.current_symbol, 4)

    def simple_heuristic_move(self, board):
        """
        Selecciona un movimiento basado en una heurística simple.
        
        :param board: El estado actual del tablero
        :return: Una tupla (fila, columna) que representa el movimiento elegido
        """
        # Lista de movimientos válidos
        valid_moves = self.valid_moves(board, self.current_symbol)
        # Seleccionar una esquina si está disponible
        corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
        # Evitar movimientos adyacentes a esquinas si las esquinas están vacías
        adjacent_to_corners = [(0, 1), (1, 0), (1, 1), (0, 6), (1, 6), (1, 7), (6, 0), (6, 1), (7, 1), (6, 6), (6, 7), (7, 6)]
        
        for move in valid_moves:
            if move in corners:
                return move
        
        safe_moves = [move for move in valid_moves if move not in adjacent_to_corners or board[move[0]][move[1]] != 0]
        
        if safe_moves:
            return random.choice(safe_moves)
        else:
            return random.choice(valid_moves)

    def valid_moves(self, board, player):
        """
        Encuentra todos los movimientos válidos para un jugador dado.
        
        :param board: El estado actual del tablero
        :param player: El jugador (1 para blanco, -1 para negro)
        :return: Una lista de tuplas (fila, columna) representando los movimientos válidos
        """
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        valid_moves = []

        for r in range(8):
            for c in range(8):
                if board[r][c] == 0:
                    for dr, dc in directions:
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < 8 and 0 <= cc < 8 and board[rr][cc] == -player:
                            while 0 <= rr < 8 and 0 <= cc < 8 and board[rr][cc] == -player:
                                rr += dr
                                cc += dc
                            if 0 <= rr < 8 and 0 <= cc < 8 and board[rr][cc] == player:
                                valid_moves.append((r, c))
                                break
        return valid_moves

    def apply_move(self, board, move, player):
        """
        Aplica un movimiento en el tablero.
        
        :param board: El estado actual del tablero
        :param move: Una tupla (fila, columna) que representa el movimiento
        :param player: El jugador (1 para blanco, -1 para negro)
        """
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        r, c = move
        board[r][c] = player

        for dr, dc in directions:
            rr, cc = r + dr, c + dc
            flips = []
            while 0 <= rr < 8 and 0 <= cc < 8 and board[rr][cc] == -player:
                flips.append((rr, cc))
                rr += dr
                cc += dc
            if 0 <= rr < 8 and 0 <= cc < 8 and board[rr][cc] == player:
                for flip in flips:
                    board[flip[0]][flip[1]] = player

    def heuristic(self, board, player):
        """
        Evalúa el tablero y devuelve una puntuación heurística.
        
        :param board: El estado actual del tablero
        :param player: El jugador (1 para blanco, -1 para negro)
        :return: La puntuación heurística del tablero
        """
        corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
        adjacent_to_corners = [(0, 1), (1, 0), (1, 1), (0, 6), (1, 6), (1, 7), (6, 0), (6, 1), (7, 1), (6, 6), (6, 7), (7, 6)]
        score = 0

        for r in range(8):
            for c in range(8):
                if board[r][c] == player:
                    if (r, c) in corners:
                        score += 50  # Alta prioridad para esquinas
                    elif (r, c) in adjacent_to_corners:
                        score -= 25  # Penalización para posiciones adyacentes a esquinas
                    elif r == 0 or r == 7 or c == 0 or c == 7:
                        score += 10  # Prioridad para bordes
                    else:
                        score += 1  # Piezas en el centro tienen menor prioridad

        return score

    def minimax_with_time_limit(self, board, player, depth):
        """
        Llama al algoritmo minimax con límite de tiempo.
        
        :param board: El tablero de juego actual
        :param player: El jugador para evaluar el tablero
        :param depth: La profundidad del árbol de decisión
        :return: Una tupla (fila, columna)
        """
        best_move = [None]
        def minimax_thread():
            best_move[0] = self.minimax(board, player, depth, -float('inf'), float('inf'), True)[1]

        thread = threading.Thread(target=minimax_thread)
        thread.start()
        thread.join(2.8)  # Esperar hasta 2.8 segundos para el cálculo
        if thread.is_alive():
            print("Minimax tardó demasiado tiempo, eligiendo movimiento heurístico.")
            thread.join(0.2)  # Un poco más de tiempo para finalizar el hilo si es posible
        return best_move[0] if best_move[0] else self.simple_heuristic_move(board)

    def minimax(self, board, player, depth, alpha, beta, maximizing):
        """
        Algoritmo minimax con poda alfa-beta.
        
        :param board: El tablero de juego actual
        :param player: El jugador para evaluar el tablero
        :param depth: La profundidad del árbol de decisión
        :param alpha: El valor alfa para poda
        :param beta: El valor beta para poda
        :param maximizing: Si el nivel actual es de maximización o minimización
        :return: Una tupla (mejor_puntaje, mejor_movimiento)
        """
        if depth == 0 or not self.valid_moves(board, player):
            return self.heuristic(board, player), None

        if maximizing:
            max_eval = -float('inf')
            best_move = None
            for move in self.valid_moves(board, player):
                new_board = [row[:] for row in board]
                self.apply_move(new_board, move, player)
                eval = self.minimax(new_board, -player, depth - 1, alpha, beta, False)[0]
                if eval > max_eval:
                    max_eval = eval
                    best_move = move
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            best_move = None
            for move in self.valid_moves(board, player):
                new_board = [row[:] for row in board]
                self.apply_move(new_board, move, player)
                eval = self.minimax(new_board, -player, depth - 1, alpha, beta, True)[0]
                if eval < min_eval:
                    min_eval = eval
                    best_move = move
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval, best_move

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Uso: python othello_player.py <session_id> <player_id>")
        sys.exit(1)

    script_name = sys.argv[0]
    session_id = sys.argv[1]
    player_id = sys.argv[2]

    print('Bienvenido ' + player_id + '!')
    othello_player = OthelloClient(player_id)
    if othello_player.connect(session_id):
        othello_player.play()
    print('¡Hasta pronto!')