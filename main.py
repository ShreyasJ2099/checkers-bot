# Setup
import copy
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
from colorama import Fore

pygame.init()
window = pygame.display.set_mode((304, 304))
pygame.display.set_caption('Checkers')

width = window.get_width()
height = window.get_height()

tSize = height / 8 if width > height else width / 8

boardColors = [(255, 230, 170), (110, 75, 0)]
colors = ['B', 'R']

pieces = []
markers = []
moveList = []

memory = {}

captureCount = 0
capLim = 20

hover = ()

turn = 0

DEPTH = 6 # 6 is best

player1 = True
player2 = False

running = True

# Classes
class Piece:
    def __init__(self, position, color):
        self.position = position
        self.color = color
        self.king = False
        x = (position[1] * tSize) + width / 16
        y = (position[0] * tSize) + width / 16
        self.xy = (x, y)
        if self.color == 'B':
            self.rgb = (50, 50, 50)
            self.rgb2 = (60, 60, 60)
        elif self.color == 'R':
            self.rgb = (255, 60, 60)
            self.rgb2 = (255, 80, 80)

    def __str__(self):
        return self.color

    def get_valids(self, board):
        nValids = []
        cValids = []
        xv = self.position[1]
        yv = self.position[0]
        for y in range(8):
            for x in range(8):
                # Normal Move
                if (((self.color == 'B' or self.king) and yv - 1 == y) or ((self.color == 'R' or self.king) and yv + 1 == y)) and (xv - 1 == x or xv + 1 == x) and board[y][x] is None:
                    nValids.append(((yv, xv), (y, x)))
                # Captures
                if board[y][x] is None and ((self.color == 'B' or self.king) and yv - 2 == y) and ((xv - 2 == x and board[yv - 1][xv - 1] is not None and board[yv - 1][xv - 1].color != self.color) or (xv + 2 == x and board[yv - 1][xv + 1] is not None and board[yv - 1][xv + 1].color != self.color)):
                    cValids.append(((yv, xv), (y, x)))
                if board[y][x] is None and ((self.color == 'R' or self.king) and yv + 2 == y) and ((xv - 2 == x and board[yv + 1][xv - 1] is not None and board[yv + 1][xv - 1].color != self.color) or (xv + 2 == x and board[yv + 1][xv + 1] is not None and board[yv + 1][xv + 1].color != self.color)):
                    cValids.append(((yv, xv), (y, x)))
        # Return
        return cValids + nValids

# Functions
def print_moves():
    os.system('clear')
    for item in moveList:
        if moveList.index(item) % 2 == 0:
            print(Fore.LIGHTBLACK_EX + item)
        else:
            print(Fore.RED + item)
    
def print_board(board):
    os.system('clear')
    for y in range(8):
        for x in range(8):
            if board[y][x] is not None:    
                print(board[y][x].__str__(), end = ' ')
            else:
                print('_', end = ' ')
        print()

def draw_board():
    for y in range(8):
        for x in range(8):
            if hover != (y, x):    
                pygame.draw.rect(window, boardColors[(y + x) % 2], (x * tSize, y * tSize, tSize, tSize))
            else:
                pygame.draw.rect(window, (20, 100, 255), (x * tSize, y * tSize, tSize, tSize))

def draw_pieces():
    pieces.clear()
    for y in range(8):
        for x in range(8):
            if board[y][x] is not None:
                piece = board[y][x]
                p = pygame.draw.circle(window, piece.rgb, piece.xy, width / 18)
                pygame.draw.circle(window, piece.rgb2, piece.xy, width / 25)
                if piece.king:
                    pygame.draw.circle(window, (255, 220, 100), piece.xy, width / 40)
                pieces.append((p, piece))

def draw_markers():
    markers.clear()
    if hover != () and board[hover[0]][hover[1]] is not None:
        valids = board[hover[0]][hover[1]].get_valids(board)
        for (sy, sx), (y, x) in valids:
            marker = pygame.draw.circle(window, (100, 100, 100), (((x * tSize) + width / 16), (y * tSize) + height / 16), width / 32)
            markers.append((marker, (y, x)))

def make_kings(board):
    for y in range(8):
        for x in range(8):
            if board[y][x] is not None:
                piece = board[y][x]
                if (piece.color == 'B' and piece.position[0] == 0) or (piece.color == 'R' and piece.position[0] == 7):
                    piece.king = True

def game_over(board, color):
    same = 0
    opp = 0
    # Scan board
    for y in range(8):
        for x in range(8):
            if board[y][x] is not None:
                if board[y][x].color == color:
                    same += 1
                else:
                    opp += 1
    # Return result
    if opp == 0 or len(get_valids(board, colors[1 - colors.index(color)])) == 0:
        return 1
    elif same == 0 or len(get_valids(board, color)) == 0:
        return -1
    else:
        return 0

def get_valids(board, color):
    valids = []
    for y in range(8):
        for x in range(8):
            if board[y][x] is not None and board[y][x].color == color:
                valids += board[y][x].get_valids(board)
    return valids

def make_move(board, sy, sx, ny, nx):
    board[ny][nx] = board[sy][sx]
    board[ny][nx].position = (ny, nx)
    board[ny][nx].xy = (((nx * tSize) + width / 16), (ny * tSize) + width / 16)
    board[sy][sx] = None
    if abs(sx - nx) == 2:
        if ny > sy:
            cy = sy + 1
        elif ny < sy:
            cy = sy - 1
        if nx > sx:
            cx = sx + 1
        elif nx < sx:
            cx = sx - 1
        board[cy][cx] = None

def make_best(color):
    global turn
    if game_over(board, color) == 0 and captureCount < capLim:  
        sTime = pygame.time.get_ticks()
        score, move = AI(board, color, 1, DEPTH, -float('inf'), float('inf'))
        eTime = pygame.time.get_ticks()
        ny, nx = move[1]
        sy, sx = move[0]
        make_move(board, sy, sx, ny, nx)
        moveList.append(f'Move: {(sx, sy)} to {(nx, ny)}, Eval: {score}, Time: {round((eTime - sTime) / 1000, 2)}')
        print_moves()
        check_capture(sx, sy, nx, ny)
        turn = 1 - turn

def AI(board, color, mod, depth, alpha, beta):
    global captureCount
    # Check terminal cases
    if game_over(board, color) == 1:
        return 100 * mod, None
    elif game_over(board, color) == -1:
        return -100 * mod, None
    elif captureCount >= capLim:
        return 0, None
    # Check depth
    if depth == 0:
        return eval(board, color) * mod, None
    # Setup
    boardHash = hash_board(board)
    best_score = -float('inf') if mod == 1 else float('inf')
    best_move = None
    valids = sort_moves(get_valids(board, color))
    # Check memory
    if boardHash in list(memory.keys()):
        return memory[boardHash][1], memory[boardHash][2]
    # Recursive
    for (sy, sx), (y, x) in valids:
        temp = copy.deepcopy(board)
        make_move(temp, sy, sx, y, x)
        prev = captureCount
        check_capture(sx, sy, x, y)
        make_kings(temp)
        score, move = AI(temp, colors[1 - colors.index(color)], -mod, depth - 1, alpha, beta)
        captureCount = prev
        if (mod == 1 and score > best_score) or (mod == -1 and score < best_score):
            best_score = score
            best_move = (sy, sx), (y, x)

        # Pruning
        if mod == 1:
            alpha = max(alpha, best_score)
        else:
            beta = min(beta, best_score)
        if alpha >= beta:
            break
    # Return
    if best_score == -0.0:
        best_score = 0.0
    if boardHash not in list(memory.keys()):
        memory[boardHash] = (mod, best_score, best_move)
    del(temp)
    return best_score, best_move

def eval(board, color):
    points = 0
    # Sum up all pieces
    for y in range(8):
        for x in range(8):
            if board[y][x] is not None:
                if board[y][x].color == color:
                    points += 1
                else:
                    points -= 1
                if board[y][x].king:
                    if board[y][x].color == color:
                        points += 5
                    else:
                        points -= 5
    # Keep pieces on back row
    if color == 'B':
        for x in range(4):
            if board[7][x*2] is not None and board[7][x*2].color == 'B':
                points += 0.25
            else:
                points -= 0.25
            if board[0][(x*2)+1] is not None and board[0][(x*2)+1].color == 'R':
                points -= 0.25
            else:
                points += 0.25
    elif color == 'R':
        for x in range(4):
            if board[0][(x*2)+1] is not None and board[0][(x*2)+1].color == 'R':
                points += 0.25
            else:
                points -= 0.25
            if board[7][x*2] is not None and board[7][x*2].color == 'B':
                points -= 0.25
            else:
                points += 0.25
    return points

def sort_moves(list):
    rlist = []
    for ((sx, sy), (ex, ey)) in list:
        # Is a capture
        if abs(sx - ex) == 2:
            rlist.append(((sx, sy), (ex, ey)))
        # Is a promote
        if ey == 0 or ey == 7:
            rlist.append(((sx, sy), (ex, ey)))
    # Add others
    for tuple in list:
        if tuple not in rlist:
            rlist.append(tuple)
    # Return
    return rlist

def hash_board(board):
    return tuple(tuple(row) for row in board)

def check_capture(sx, sy, ex, ey):
    global captureCount
    if abs(sx - ex) == 2:
        captureCount = 0
    else:
        captureCount += 1

# On start
RP1 = Piece((0, 1), 'R')
RP2 = Piece((0, 3), 'R')
RP3 = Piece((0, 5), 'R')
RP4 = Piece((0, 7), 'R')
RP5 = Piece((1, 0), 'R')
RP6 = Piece((1, 2), 'R')
RP7 = Piece((1, 4), 'R')
RP8 = Piece((1, 6), 'R')
BP1 = Piece((5, 0), 'B')
BP2 = Piece((5, 2), 'B')
BP3 = Piece((5, 4), 'B')
BP4 = Piece((5, 6), 'B')
BP5 = Piece((6, 1), 'B')
BP6 = Piece((6, 3), 'B')
BP7 = Piece((6, 5), 'B')
BP8 = Piece((6, 7), 'B')
RP9 = Piece((2, 1), 'R')
RP10 = Piece((2, 3), 'R')
RP11 = Piece((2, 5), 'R')
RP12 = Piece((2, 7), 'R')
BP9 = Piece((7, 0), 'B')
BP10 = Piece((7, 2), 'B')
BP11 = Piece((7, 4), 'B')
BP12 = Piece((7, 6), 'B')

board = [
    [None, RP1, None, RP2, None, RP3, None, RP4],
    [RP5, None, RP6, None, RP7, None, RP8, None],
    [None, RP9, None, RP10, None, RP11, None, RP12],
    [None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None],
    [BP1, None, BP2, None, BP3, None, BP4, None],
    [None, BP5, None, BP6, None, BP7, None, BP8],
    [BP9, None, BP10, None, BP11, None, BP12, None]
]

while running:
    # Game Over
    if game_over(board, colors[turn]) != 0 or captureCount >= capLim:
        running = False
    make_kings(board)
    # Draw
    window.fill((0, 0, 0))
    draw_board()
    draw_pieces()
    draw_markers()
    pygame.display.update()
    # Run AI
    if (turn == 0 and not player1) or (turn == 1 and not player2):
        make_best(colors[turn])
    # Events
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN and ((turn == 0 and player1) or (turn == 1 and player2)):
            # Piece is pressed
            for image, piece in pieces:
                if image.collidepoint(pygame.mouse.get_pos()) and ((piece.color == 'B' and turn == 0) or (piece.color == 'R' and turn == 1)):
                    hover = piece.position
            # Marker pressed
            for marker, pos in markers:
                if marker.collidepoint(pygame.mouse.get_pos()):
                    ny, nx = pos
                    sy, sx = hover[0], hover[1]
                    make_move(board, sy, sx, ny, nx)
                    hover = ()
                    moveList.append(f'Move: {(sx, sy)} to {(nx, ny)}, Eval: {eval(board, colors[turn])}')
                    check_capture(sx, sy, nx, ny)
                    turn = 1 - turn
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                print_board(board)

# Game Over Screen
window.fill((0, 0, 0))
font = pygame.font.SysFont('Sans', round(width / 10))

if game_over(board, 'R') == 1:
    t = font.render('Red Wins!', False, (255, 0, 0))
elif game_over(board, 'B') == 1:
    t = font.render('Black Wins!', False, (70, 70, 70))
else:
    t = font.render("It's a draw.", False, (255, 255, 255))

window.blit(t, (0, 0))

while True:
    pygame.display.update()
