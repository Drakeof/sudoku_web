from flask import Flask, render_template, jsonify, request
import random
import numpy as np

# Inicialización de la aplicación Flask
app = Flask(__name__)
app.config['PROJECT_NAME'] = 'Sudoku Web'

class Sudoku:
    def __init__(self, level, size):
        """
        Inicializa un nuevo juego de Sudoku.
        
        :param level: Nivel de dificultad del juego ('easy', 'medium', 'hard')
        :param size: Tamaño del tablero (2 para 4x4, 3 para 9x9, 4 para 16x16)
        """
        self.size = int(size)
        self.board = self.generate_board(level)
        self.solution = [row[:] for row in self.board]  # Copia la solución completa
        self.remove_numbers(self.board, level)

    def generate_board(self, level):
        """
        Genera un tablero de Sudoku completo y válido.
        
        :param level: Nivel de dificultad (no se usa en esta función, pero se mantiene para consistencia)
        :return: Tablero de Sudoku completo
        """
        if self.size == 3:
            # Generar matriz base 3x3
            base_matrix = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
            np.random.shuffle(base_matrix)
            np.random.shuffle(base_matrix.T)
            
            # Generar matriz completa 9x9
            board = np.zeros((9, 9), dtype=int)
            for i in range(3):
                for j in range(3):
                    board[i*3:(i+1)*3, j*3:(j+1)*3] = (base_matrix + 3*i + j*3) % 9 + 1
            
            # Aplicar permutaciones aleatorias
            for _ in range(10):
                if random.choice([True, False]):
                    i, j = random.randint(0, 2), random.randint(0, 2)
                    board[i*3:(i+1)*3], board[j*3:(j+1)*3] = board[j*3:(j+1)*3].copy(), board[i*3:(i+1)*3].copy()
                else:
                    i, j = random.randint(0, 2), random.randint(0, 2)
                    board[:, i*3:(i+1)*3], board[:, j*3:(j+1)*3] = board[:, j*3:(j+1)*3].copy(), board[:, i*3:(i+1)*3].copy()
            
            return board.tolist()
        else:
            board = [[0 for _ in range(self.size ** 2)] for _ in range(self.size ** 2)]
            self.solve_board(board)
            return board

    def solve_board(self, board):
        """
        Resuelve el tablero de Sudoku utilizando backtracking.
        
        :param board: Tablero de Sudoku a resolver
        :return: True si se encontró una solución, False en caso contrario
        """
        empty = self.find_empty(board)
        if not empty:
            return True
        row, col = empty
        for num in range(1, self.size ** 2 + 1):
            if self.is_valid_move(board, row, col, num):
                board[row][col] = num
                if self.solve_board(board):
                    return True
                board[row][col] = 0
        return False

    def find_empty(self, board):
        """
        Encuentra la primera celda vacía en el tablero.
        
        :param board: Tablero de Sudoku
        :return: Tupla (fila, columna) de la celda vacía, o None si no hay celdas vacías
        """
        for i in range(self.size ** 2):
            for j in range(self.size ** 2):
                if board[i][j] == 0:
                    return (i, j)
        return None

    def is_valid_move(self, board, row, col, num):
        """
        Verifica si es válido colocar un número en una celda específica.
        
        :param board: Tablero de Sudoku
        :param row: Fila de la celda
        :param col: Columna de la celda
        :param num: Número a verificar
        :return: True si el movimiento es válido, False en caso contrario
        """
        # Verifica la fila
        if num in board[row]:
            return False
        
        # Verifica la columna
        if num in [board[i][col] for i in range(self.size ** 2)]:
            return False
        
        # Verifica el cuadrado
        start_row, start_col = self.size * (row // self.size), self.size * (col // self.size)
        for i in range(start_row, start_row + self.size):
            for j in range(start_col, start_col + self.size):
                if board[i][j] == num:
                    return False
        return True

    def remove_numbers(self, board, level):
        """
        Elimina números del tablero para crear un puzzle de Sudoku.
        
        :param board: Tablero de Sudoku completo
        :param level: Nivel de dificultad ('easy', 'medium', 'hard')
        """
        difficulty = {
            'easy': 0.3,
            'medium': 0.5,
            'hard': 0.7
        }
        cells_to_remove = int((self.size ** 4) * difficulty[level])
        while cells_to_remove > 0:
            row = random.randint(0, self.size ** 2 - 1)
            col = random.randint(0, self.size ** 2 - 1)
            if board[row][col] != 0:
                board[row][col] = 0
                cells_to_remove -= 1

@app.route('/')
def index():
    """Renderiza la página principal del juego."""
    return render_template('index.html')

@app.route('/new_game', methods=['POST'])
def new_game():
    """
    Crea un nuevo juego de Sudoku.
    
    :return: JSON con el nuevo tablero de juego
    """
    data = request.json
    size = int(data['size'])
    level = data['level']
    sudoku = Sudoku(level, size)
    return jsonify(board=sudoku.board, solution=sudoku.solution)

@app.route('/check_solution', methods=['POST'])
def check_solution():
    """
    Verifica si la solución propuesta por el usuario es correcta.
    
    :return: JSON con el resultado de la verificación
    """
    data = request.json
    board = data['board']
    size = int(len(board) ** 0.5)
    sudoku = Sudoku('easy', size)
    
    # Verifica si el tablero está completamente lleno
    if any(0 in row for row in board):
        return jsonify(valid=False, message="El tablero no está completamente lleno.")
    
    # Verifica cada celda
    for i in range(size ** 2):
        for j in range(size ** 2):
            num = board[i][j]
            board[i][j] = 0  # Elimina temporalmente el número para verificar si es válido
            if not sudoku.is_valid_move(board, i, j, num):
                board[i][j] = num  # Vuelve a colocar el número antes de retornar
                return jsonify(valid=False, message="Hay un conflicto en la fila {}, columna {}.".format(i+1, j+1))
            board[i][j] = num  # Vuelve a colocar el número
    
    return jsonify(valid=True, message="¡Felicidades! Has resuelto el Sudoku correctamente.")

@app.route('/get_solution', methods=['POST'])
def get_solution():
    """
    Obtiene la solución completa del Sudoku actual.
    
    :return: JSON con la solución del Sudoku
    """
    data = request.json
    size = int(data['size'])
    level = data['level']
    board = data.get('board', None)
    
    if board is None:
        # Si no se proporciona un tablero, crear uno nuevo
        sudoku = Sudoku(level, size)
        solution = sudoku.solution
    else:
        # Si se proporciona un tablero, resolverlo
        sudoku = Sudoku(level, size)
        sudoku.board = board
        sudoku.solve_board(sudoku.board)
        solution = sudoku.board
    
    return jsonify(solution=solution)

@app.route('/check_cell', methods=['POST'])
def check_cell():
    """
    Verifica si el número colocado en una celda es correcto.
    
    :return: JSON con el resultado de la verificación
    """
    data = request.json
    row = data['row']
    col = data['col']
    num = int(data['num'])  # Asegurarse de que num sea un entero
    solution = data['solution']
    size = int(len(solution) ** 0.5)
    
    # Verifica que el número ingresado sea válido para el tamaño del tablero
    if num < 1 or num > size ** 2:
        return jsonify(correct=False, message=f"Número inválido. Debe estar entre 1 y {size ** 2}")
    
    is_correct = solution[row][col] == num
    return jsonify(correct=is_correct)

if __name__ == '__main__':
    app.run(debug=True)
