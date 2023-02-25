
import os.path
from statistics import mean, median
import time
import copy
import pygame
import sys
import pathlib
import tkinter
import tkinter.filedialog

path = str(pathlib.Path(__file__).parent.resolve())
INCEPATOR_DEPTH = 1
MEDIU_DEPTH = 2
AVANSAT_DEPTH = 3

# Clasa pentru joc
class Game:
    COLUMNS = 5
    Player1 = 'a'
    Player2 = 'n'
    EMPTY = '#'

    alone = None

    grid_cells = None
    end_game_button = None
    restart_game_button = None
    undo_button = None

    selected_square = None
    available_squares = None

    matrix = None


    def __init__(self, table=None):
        # Se initiaza tabla de joc cu piese in pozitiile default
        self.calculated_moves = dict()
        self.calculated_piece_moves = dict()
        if table is not None:
            self.matrix = table
            return
        self.matrix = [[self.EMPTY for _ in range(self.COLUMNS)] for _ in range(self.COLUMNS)]
        self.matrix[0] = [self.Player1 for i in range(self.COLUMNS)]
        self.matrix[1][0] = self.Player1
        self.matrix[1][4] = self.Player1
        self.matrix[4] = [self.Player2 for i in range(self.COLUMNS)]
        self.matrix[3][0] = self.Player2
        self.matrix[3][4] = self.Player2

    def draw_grid(self, marked_line=None, marked_column=None, marked_player=None):
        # Se deseneaza tabla de joc in pygame
        for ind in range(self.COLUMNS ** 2):
            line = ind // self.COLUMNS
            column = ind % self.COLUMNS

            # La miscarea mouseului apare pe ce casuta dam hover cu gri
            if column == marked_column and line == marked_line:
                color = (200, 200, 200)
            else:
                color = (255, 255, 255)
            
            # Daca un jucator castiga ii facem funalul de la casute cu verde
            if self.matrix[line][column] == marked_player:
                color = (24, 190, 21)

            # Daca o piesa este selectata ii facem fundalul gri mai inchis
            if ind == self.selected_square:
                color = (150, 150, 150)

            # Afisam unde poate fi putata o piesa
            if self.available_squares and (line, column) in self.available_squares:
                color = (122, 230, 141)

            # Afisam imaginile pieselor
            pygame.draw.rect(self.display, color, self.grid_cells[ind])
            piece_img = None
            if self.matrix[line][column] == 'a':
                piece_img = self.a_img
            elif self.matrix[line][column] == 'n':
                piece_img = self.n_img
            if piece_img:
                self.display.blit(piece_img,
                                  (column * (self.cell_size + 1), line * (self.cell_size + 1) + self.top_offset))

        self.undo_button.draw()
        self.end_game_button.draw()
        self.restart_game_button.draw()
        pygame.display.update()

    def draw_square(self, ind, symbol, valid):
        # Functie care este apelata cand e apasat o piesa
        line = ind // self.COLUMNS
        column = ind % self.COLUMNS

        # Face cam la fel ce face si draw_grid, numai ca face asta la apasarea piesei, nu la miscarea mouseului
        if self.matrix[line][column] != symbol:
            return

        if self.available_squares:
            for i in self.available_squares:
                aux = i[0] * 5 + i[1]
                pygame.draw.rect(self.display, (255, 255, 255), self.grid_cells[aux])

        validSet = None
        self.available_squares = None
        validSet = set([i[1] for i in valid])
        self.available_squares = validSet

        if self.selected_square:
            auxline = self.selected_square // self.COLUMNS
            auxcolumn = self.selected_square % self.COLUMNS
            pygame.draw.rect(self.display, (255, 255, 255), self.grid_cells[self.selected_square])
            if symbol == 'a':
                piece_img = self.a_img
            elif symbol == 'n':
                piece_img = self.n_img
            if piece_img:
                self.display.blit(piece_img, (auxcolumn * (self.cell_size + 1), auxline * (self.cell_size + 1) + self.top_offset))

        self.selected_square = ind

        pygame.draw.rect(self.display, (150, 150, 150), self.grid_cells[ind])

        piece_img = None
        if symbol == 'a':
            piece_img = self.a_img
        elif symbol == 'n':
            piece_img = self.n_img
        if piece_img:
            self.display.blit(piece_img, (column * (self.cell_size + 1), line * (self.cell_size + 1) + self.top_offset))

        for ind in range(self.COLUMNS ** 2):
            line = ind // self.COLUMNS
            column = ind % self.COLUMNS

            if (line, column) in validSet:
                pygame.draw.rect(self.display, (122, 230, 141), self.grid_cells[ind])

        pygame.display.update()

    @classmethod
    def opposite_player(cls, player):
        # Se genereaza jucaotorul opus jucatorului curent
        return cls.Player2 if player == cls.Player1 else cls.Player1

    @classmethod
    def initialize(cls, display, cell_size=100):
        # Se initilaizeaza butoanele de sus si se loadeaza imaginile
        def load_image(name):
            img = pygame.image.load(os.path.join(path + "\\assets", name))
            return pygame.transform.scale(img, (cell_size, cell_size))

        cls.end_game_button = Button(display=display, left=10, top=10, w=80, h=30, text="Exit",
                                     background_color=(200, 0, 0))
        cls.restart_game_button = Button(display=display, left=110, top=10, w=80, h=30, text="Restart",
                                background_color=(200, 0, 0), background_color_hover=(200, 0, 0))
        cls.undo_button = Button(display=display, left=210, top=10, w=80, h=30, text="Undo",
                                background_color=(200, 0, 0), background_color_hover=(200, 0, 0))
        cls.top_offset = 50
        cls.display = display
        cls.cell_size = cell_size
        cls.a_img = load_image("a.png")
        cls.n_img = load_image("n.png")
        cls.grid_cells = []
        for line in range(Game.COLUMNS):
            for column in range(Game.COLUMNS):
                square = pygame.Rect(column * (cell_size + 1), line * (cell_size + 1) + cls.top_offset, cell_size,
                                     cell_size)
                cls.grid_cells.append(square)

    def final(self):
        # Se verifica conditiile de final din cerinta
        # Se returneaza jucatorul castigator, False daca nu s-a indeplinit conditia sau 'draw' daca e egal

        if len(self.moves(self.Player1)) == 0 and len(self.moves(self.Player2)) == 0:
            return 'draw'
            
        player1win, player2win = True, True
        for x in range(self.COLUMNS):
            for y in range(self.COLUMNS):
                if self.matrix[x][y] == self.Player1:
                    if self.has_neighbor(self.Player1, x, y):
                        player1win = False
                    if not self.has_enemy_neighbor(self.Player1, x, y):
                        player1win = False
                elif self.matrix[x][y] == self.Player2:
                    if self.has_neighbor(self.Player2, x, y):
                        player2win = False
                    if not self.has_enemy_neighbor(self.Player2, x, y):
                        player2win = False

        if player1win:
            return self.Player1
        elif player2win:
            return self.Player2

        # if len(self.moves(self.Player1)) == 0:
        #     return self.Player2
        # elif len(self.moves(self.Player2)) == 0:
        #     return self.Player1

        return False 

    def valid_spot(self, x, y):
        # Verificam daca o pozitie e in grid
        return 0 <= x < self.COLUMNS and 0 <= y < self.COLUMNS

    def piece_moves(self, x, y, player):
        # Se genereaza toate miscarile posibile ale unei piese de la coordonatele x y
        moves = []

        # Daca n-are niciun vecin nu poate face nimic piesa
        if not self.has_neighbor(player, x, y):
            return moves

        # Vedem toate glisarile in toate partile pana da de o piesa inamica
        # Sus jos

        nx, ny = x - 1, y

        while self.valid_spot(nx, ny) and self.matrix[nx][ny] != player and self.matrix[nx][ny] == self.EMPTY:
            current_matr = copy.deepcopy(self.matrix)
            current_matr[nx][ny] = current_matr[x][y]
            current_matr[x][y] = Game.EMPTY
            moves.append((Game(current_matr), (nx, ny)))
            nx -= 1

        nx, ny = x + 1, y

        while self.valid_spot(nx, ny) and self.matrix[nx][ny] != player and self.matrix[nx][ny] == self.EMPTY:
            current_matr = copy.deepcopy(self.matrix)
            current_matr[nx][ny] = current_matr[x][y]
            current_matr[x][y] = Game.EMPTY
            moves.append((Game(current_matr), (nx, ny)))
            nx += 1

        # Dreapta stanga

        nx, ny = x , y + 1

        while self.valid_spot(nx, ny) and self.matrix[nx][ny] != player and self.matrix[nx][ny] == self.EMPTY:
            current_matr = copy.deepcopy(self.matrix)
            current_matr[nx][ny] = current_matr[x][y]
            current_matr[x][y] = Game.EMPTY
            moves.append((Game(current_matr), (nx, ny)))
            ny += 1

        nx, ny = x , y - 1

        while self.valid_spot(nx, ny) and self.matrix[nx][ny] != player and self.matrix[nx][ny] == self.EMPTY:
            current_matr = copy.deepcopy(self.matrix)
            current_matr[nx][ny] = current_matr[x][y]
            current_matr[x][y] = Game.EMPTY
            moves.append((Game(current_matr), (nx, ny)))
            ny -= 1

        # Diagonale

        nx, ny = x - 1, y - 1

        while self.valid_spot(nx, ny) and self.matrix[nx][ny] != player and self.matrix[nx][ny] == self.EMPTY:
            current_matr = copy.deepcopy(self.matrix)
            current_matr[nx][ny] = current_matr[x][y]
            current_matr[x][y] = Game.EMPTY
            moves.append((Game(current_matr), (nx, ny)))
            nx -= 1
            ny -= 1

        nx, ny = x + 1, y + 1

        while self.valid_spot(nx, ny) and self.matrix[nx][ny] != player and self.matrix[nx][ny] == self.EMPTY:
            current_matr = copy.deepcopy(self.matrix)
            current_matr[nx][ny] = current_matr[x][y]
            current_matr[x][y] = Game.EMPTY
            moves.append((Game(current_matr), (nx, ny)))
            nx += 1
            ny += 1

        nx, ny = x - 1, y + 1

        while self.valid_spot(nx, ny) and self.matrix[nx][ny] != player and self.matrix[nx][ny] == self.EMPTY:
            current_matr = copy.deepcopy(self.matrix)
            current_matr[nx][ny] = current_matr[x][y]
            current_matr[x][y] = Game.EMPTY
            moves.append((Game(current_matr), (nx, ny)))
            nx -= 1
            ny += 1
            
        nx, ny = x + 1, y - 1

        while self.valid_spot(nx, ny) and self.matrix[nx][ny] != player and self.matrix[nx][ny] == self.EMPTY:
            current_matr = copy.deepcopy(self.matrix)
            current_matr[nx][ny] = current_matr[x][y]
            current_matr[x][y] = Game.EMPTY
            moves.append((Game(current_matr), (nx, ny)))
            nx += 1
            ny -= 1

        self.has_any_neighbor()

        # Daca un jucator are o piesa fara niciun vecin, se pot face mutari numai pana la acea piesa
        if self.alone and self.alone[2] == player:
            newmoves = []
            sx, sy = self.alone[0], self.alone[1]
            for i in range(len(moves)):
                mx, my = moves[i][1][0], moves[i][1][1]
                if (mx - 1 == sx or mx + 1 == sx or mx == sx) and (my - 1 == sy or my + 1 == sy or my == sy):
                    newmoves.append(moves[i])
            moves = copy.deepcopy(newmoves)

        self.calculated_piece_moves[(x, y, player)] = copy.deepcopy(moves)
        return moves

    def has_neighbor(self, player, x, y):
        # Verificam daca piesa are vecin prieten
        dx, dy = [0, 1, -1, 0, -1, 1, -1, 1], [1, 0, 0, -1, 1, 1, -1, -1]
        for k in range(len(dy)):
            if x + dx[k] >= 0 and x + dx[k] < self.COLUMNS and y + dy[k] >= 0 and y + dy[k] < self.COLUMNS and self.matrix[x+dx[k]][y+dy[k]] == player:
                return True
        return False
    
    def has_enemy_neighbor(self, player, x, y):
        # Verificam daca piesa are vecin inamic
        dx, dy = [0, 1, -1, 0, -1, 1, -1, 1], [1, 0, 0, -1, 1, 1, -1, -1]
        for k in range(len(dy)):
            if x + dx[k] >= 0 and x + dx[k] < self.COLUMNS and y + dy[k] >= 0 and y + dy[k] < self.COLUMNS and self.matrix[x+dx[k]][y+dy[k]] == self.opposite_player(player):
                return True
        return False

    def has_any_neighbor(self):
        # Verificam daca piesa are orice vecin
        dx, dy = [0, 1, -1, 0, -1, 1, -1, 1], [1, 0, 0, -1, 1, 1, -1, -1]
        for x in range(self.COLUMNS):
            for y in range(self.COLUMNS):
                if self.matrix[x][y] != self.EMPTY:
                    check = True
                    for k in range(len(dy)):
                        if x + dx[k] >= 0 and x + dx[k] < self.COLUMNS and y + dy[k] >= 0 and y + dy[k] < self.COLUMNS and self.matrix[x+dx[k]][y+dy[k]] != self.EMPTY:
                            check = False
                    if check:
                        self.alone = (x, y, self.matrix[x][y])
                        return
        self.alone = None

    def can_move(self, player):
        # Verificam daca un jucator poate muta
        self.has_any_neighbor()
        if self.alone == None:
            return True
        if len(self.moves(player)) == 0:
            return False
        return True

    def moves(self, player):
        # Se genereaza toate miscarile posibile ale pieselor unui jucator
        moves = []
        for i in range(self.COLUMNS):
            for j in range(self.COLUMNS):
                if self.matrix[i][j] == player and self.has_neighbor(player, i, j) == True:
                    moves.extend(self.piece_moves(i, j, player))
                elif self.has_neighbor(player, i, j) == False:
                    moves.extend([])
        
        if not moves:
            return moves

        self.calculated_moves[player] = copy.deepcopy(moves)
        return moves

    def estimate_score_1(self, depth=0):
        # Functia de estimare scor 1
        # Scorul se va mari daca o piesa nu are langa ea o piesa prietena, dar are o piesa inamica
        # Motivul este ca asta este conditia de incheiere a jocului, ca fiecare piesa prietena sa fie langa una inamica
        # Dar sa nu fie piese prietene una langa alta
        # Totusi, nu se scade daca doua piese prietene sunt una langa alta, caci poate fi de ajutor si asta pt mutari ulterioare
        t_final = self.final()
        if t_final == self.Player2:
            return 1000 + depth
        elif t_final == self.Player1:
            return -1000 - depth
        elif t_final == 'draw':
            return 0
        else:
            player1score, player2score = 0, 0
            for x in range(self.COLUMNS):
                for y in range(self.COLUMNS):
                    if self.matrix[x][y] == self.Player1:
                        if not self.has_neighbor(self.Player1, x, y):
                            player1score += 1
                        if self.has_enemy_neighbor(self.Player1, x, y):
                            player1score += 1
                    elif self.matrix[x][y] == self.Player2:
                        if not self.has_neighbor(self.Player2, x, y):
                            player2score += 1
                        if self.has_enemy_neighbor(self.Player2, x, y):
                            player2score += 1

            return player2score - player1score

    def estimate_score_2(self, depth=0):
        # Asemanator cu 1, numai ca se ia in calcul si daca o piesa nu are niciun vecin
        # Acel caz e foarte defavorabil, si se scad 2 puncte, pentru ca trebuie mutata o alta piesa neaparat la ea sa o ajute
        # Se ia in calcul si daca un jucator nu poate face nicio miscare, iarasi e foarte rau si se scad puncte
        t_final = self.final()
        if t_final == self.Player2:
            return 1000 + depth
        elif t_final == self.Player1:
            return -1000 - depth
        elif t_final == 'draw':
            return 0
        else:
            player1score, player2score = 0, 0
            for x in range(self.COLUMNS):
                for y in range(self.COLUMNS):
                    if self.matrix[x][y] == self.Player1:
                        if not self.has_neighbor(self.Player1, x, y):
                            player1score += 1
                        if self.has_enemy_neighbor(self.Player1, x, y):
                            player1score += 1
                        if not self.has_neighbor(self.Player1, x, y) and not self.has_enemy_neighbor(self.Player1, x, y):
                            player1score -= 2
                        if not self.can_move(self.Player1):
                            player1score -= 2
                    elif self.matrix[x][y] == self.Player2:
                        if not self.has_neighbor(self.Player2, x, y):
                            player2score += 1
                        if self.has_enemy_neighbor(self.Player2, x, y):
                            player2score += 1
                        if not self.has_neighbor(self.Player2, x, y) and not self.has_enemy_neighbor(self.Player2, x, y):
                            player2score -= 2
                        if not self.can_move(self.Player2):
                            player2score -= 2

            return player2score - player1score

    def estimate_score(self, depth, estimate_function="2"):
        # Se alege o functie de estimare
        if estimate_function == "1":
            return self.estimate_score_1(depth)
        return self.estimate_score_2(depth)

    def to_string(self):
        # Afisarea tablei de joc
        sir = "\n"
        for i in range(self.COLUMNS):
            sir += " ".join(self.matrix[i]) + "\n"
        return sir

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return self.to_string()


# Clasa pentru stare din algoritmi
class State:
    """
    Clasa folosita de algoritmii minmax si alpha-beta
    O instanta din clasa state este un nod din arborele minmax
    Are ca proprietate table de joc
    Functioneaza cu conditia ca in cadrul clasei Game sa fie definiti Player1 si Player2 (cei doi jucatori posibili)
    De asemenea cere ca in clasa Game sa fie definita si o metoda numita moves() care ofera lista cu configuratiile posibile in urma mutarii unui player
    """

    def __init__(self, game_table, j_curent, depth, parent=None, estimate=None, nodes=0):
        # Initializarea starii
        self.game_table = game_table
        self.j_curent = j_curent

        self.nodes = nodes

        # adancimea in arborele de stari
        self.depth = depth

        # estimarea favorabilitatii starii (daca e finala) sau al celei mai bune stari-fiice (pentru jucatorul curent)
        self.estimate = estimate

        # lista de moves posibile (tot de tip State) din starea curenta
        self.possible_moves = []

        # cea mai buna move din lista de moves posibile pentru jucatorul curent
        # e de tip State (cel mai bun succesor)
        self.chosen_state = None

    def moves(self):
        # Toate mutarile posibile
        l_mutari = self.game_table.moves(self.j_curent)  # lista de informatii din nodurile succesoare
        juc_opus = Game.opposite_player(self.j_curent)

        # mai jos calculam lista de noduri-fii (succesori)
        l_stari_mutari = [State(move[0], juc_opus, self.depth - 1, parent=self) for move in l_mutari]

        return l_stari_mutari

    def write(self, name):
        # Se scrie in fisier starea cu informatiile trebuincioase
        fout = open(path + "\\saves\\" + name + ".txt", "w")
        fout.write(str(self.j_curent) + "\n")
        fout.write(str(self.nodes) + "\n")
        fout.write(str(self.depth) + "\n")
        fout.write(str(self.estimate) + "\n")
        for i in self.game_table.matrix:
            for j in i:
                fout.write(j)

    def __str__(self):
        sir = str(self.game_table) + "(Juc curent:" + self.j_curent + ")\n"
        return sir


# Clasa pentru buton
class Button:
    def __init__(self, display=None, left=0, top=0, w=0, h=0, background_color=(53, 80, 115),
                 background_color_hover=(89, 134, 194), text="", font="arial", fontDimensiune=16,
                 culoareText=(255, 255, 255),
                 value=None):
        self.left = None
        self.top = None
        self.display = display
        self.background_color = background_color
        self.background_color_hover = background_color_hover
        self.text = text
        self.font = font
        self.w = w
        self.h = h
        self.selectat = False
        self.fontDimensiune = fontDimensiune
        self.culoareText = culoareText
        # creez obiectul font
        fontObj = pygame.font.SysFont(self.font, self.fontDimensiune)
        self.rendered_text = fontObj.render(self.text, True, self.culoareText)
        self.dreptunghi = pygame.Rect(left, top, w, h)
        # aici centram textul
        self.text_rectangle = self.rendered_text.get_rect(center=self.dreptunghi.center)
        self.value = value

    def select(self, sel):
        self.selectat = sel
        self.draw()

    def select_by_coord(self, coord):
        # Se verifica daca se face clickpe buton
        if self.dreptunghi.collidepoint(coord):
            self.select(True)
            return True
        return False

    def update_rectangle(self):
        self.dreptunghi.left = self.left
        self.dreptunghi.top = self.top
        self.text_rectangle = self.rendered_text.get_rect(center=self.dreptunghi.center)

    def draw(self):
        # Se pune butonul in joc
        color = self.background_color_hover if self.selectat else self.background_color
        pygame.draw.rect(self.display, color, self.dreptunghi)
        self.display.blit(self.rendered_text, self.text_rectangle)


# Clasa pentru un grup de butoane
class GrupButoane:
    def __init__(self, buttons_list=None, selected_index=0, spatiuButoane=5, left=0, top=0):
        if buttons_list is None:
            buttons_list = []
        self.buttons_list = buttons_list
        self.selected_index = selected_index
        self.buttons_list[self.selected_index].selectat = True
        self.top = top
        self.left = left
        left_current = self.left
        for b in self.buttons_list:
            b.top = self.top
            b.left = left_current
            b.update_rectangle()
            left_current += (spatiuButoane + b.w)

    def select_by_coord(self, coord):
        for ib, b in enumerate(self.buttons_list):
            if b.select_by_coord(coord):
                self.buttons_list[self.selected_index].select(False)
                self.selected_index = ib
                return True
        return False

    def draw(self):
        for b in self.buttons_list:
            b.draw()

    def get_value(self):
        return self.buttons_list[self.selected_index].value


# Clasa care scrie in consola informatii
class Write:
    def __init__(self):
        self.starttime = time.time()
        self.currenttime = time.time()
        self.minnodes = sys.maxsize
        self.maxnodes = -1
        self.nodes = []
        self.moves_a = 0
        self.moves_n = 0
        self.computer_time = []
        self.current_state = None

    def get_current_time_diff(self, time_start=None):
        # Se calculeaza timpul scurs
        if time_start is None:
            time_start = self.starttime
        return round((time.time() - time_start) * 1000)

    def update_moves(self, current_state):
        # Se incrementeaza miscarile
        if current_state.j_curent == 'n':
            self.moves_n += 1
        if current_state.j_curent == 'a':
            self.moves_a += 1

    def update_nodes(self, nodes):
        # Se afiseaza cate noduri s-au generat si se modifica atributele
        print(f"\nS-au generat {nodes} noduri")
        self.minnodes = min(self.minnodes, nodes)
        self.maxnodes = max(self.maxnodes, nodes)
        self.nodes.append(nodes)

    def update_current_state(self, new_state, player="calculator"):
        # Se afiseaza dupa fiecare miscare informatii
        timp = self.get_current_time_diff(self.currenttime)
        if player == "calculator":
            self.computer_time.append(timp)
        print(f"{player.capitalize()}ului i-a luat {timp} milisecunde sa faca miscarea.")
        print(f"Scor: {new_state.game_table.estimate_score(0)}")
        print(f"\nTabla dupa mutarea {player}ului: ")
        print(str(new_state))
        self.current_state = new_state
        self.current_time = time.time()

    def final(self):
        # Se afiseaza statisticile finale jocului
        txt = "\nStatistici finale:"
        txt += f"\nJocul a durat {self.get_current_time_diff()} milisecunde."
        txt += f"\nAlb a facut {self.moves_a} mutari, negru a facut {self.moves_n} mutari."

        if self.moves_a == 0 or self.moves_n == 0:
            return txt

        txt += f"\nS-a generat un număr minim de {self.minnodes} noduri și maxim de {self.maxnodes} noduri."
        txt += f"\nMediana numarului de noduri generate e {median(self.nodes)} si media de {mean(self.nodes)} noduri"
        txt += f"\nCalculatorul s-a gandit minim {min(self.computer_time)} si maxim {max(self.computer_time)} milisecunde."
        txt += f"\nMediana timpului sau de gandire e {median(self.computer_time)} si media de {mean(self.computer_time)} milisecunde."
        return txt


# Minimax
def min_max(state, estimate_function="1"):
    # daca sunt la o frunza in arborele minmax sau la o state finala
    if state.depth == 0 or state.game_table.final():
        state.estimate = state.game_table.estimate_score(state.depth, estimate_function)
        state.nodes = 1
        return state

    # calculez toate mutarile posibile din starea curenta
    state.possible_moves = state.moves()

    # aplic algoritmul minmax pe toate mutarile posibile (calculand astfel subarborii lor)
    # expandez(constr subarb) fiecare nod x din moves posibile
    moves_with_estimate = [min_max(x, estimate_function) for x in state.possible_moves]
    state.nodes += sum([x.nodes for x in moves_with_estimate])

    if state.j_curent == Game.Player2:
        # daca jucatorul e Player2 aleg starea-fiica cu estimarea maxima
        state.chosen_state = max(moves_with_estimate, key=lambda x: x.estimate)
        # def f(x): return x.estimate -----> key=f
    else:
        # daca jucatorul e Player1 aleg starea-fiica cu estimarea minima
        state.chosen_state = min(moves_with_estimate, key=lambda x: x.estimate)

    state.estimate = state.chosen_state.estimate
    return state


# Alphabeta
def alpha_beta(alpha, beta, state, estimate_function="1"):
    if state.depth == 0 or state.game_table.final():
        state.estimate = state.game_table.estimate_score(state.depth, estimate_function)
        state.nodes = 1
        return state

    if alpha > beta:
        return state  # este intr-un interval invalid deci nu o mai procesez

    state.possible_moves = state.moves()

    if state.j_curent == Game.Player2:
        current_estimation = float('-inf')  # in aceasta variabila calculam maximul

        # Ordonarea succesorilor înainte de expandare (bazat pe estimare)
        state.possible_moves.sort(key=lambda x: x.game_table.estimate_score(state.depth, estimate_function), reverse=True)

        for move in state.possible_moves:
            # calculează estimarea pentru starea nouă, realizând subarborele
            # aici construim subarborele pentru new_state
            new_state = alpha_beta(alpha, beta, move, estimate_function)
            state.nodes += new_state.nodes
            if current_estimation < new_state.estimate:
                state.chosen_state = new_state
                current_estimation = new_state.estimate
            if alpha < new_state.estimate:
                alpha = new_state.estimate
                if alpha >= beta:
                    break

    elif state.j_curent == Game.Player1:
        current_estimation = float('inf')

        # Ordonarea succesorilor înainte de expandare (bazat pe estimare)
        state.possible_moves.sort(key=lambda x: x.game_table.estimate_score(state.depth, estimate_function))

        for move in state.possible_moves:
            # calculează estimarea
            # aici construim subarborele pentru new_state
            new_state = alpha_beta(alpha, beta, move, estimate_function)
            state.nodes += new_state.nodes
            if current_estimation > new_state.estimate:
                state.chosen_state = new_state
                current_estimation = new_state.estimate
            if beta > new_state.estimate:
                beta = new_state.estimate
                if alpha >= beta:
                    break

    state.estimate = state.chosen_state.estimate

    return state


# Se afiseaza daca s-a terminat jocul
def show_if_final(current_state):
    final = current_state.game_table.final()
    if final:
        if final == "draw":
            print("Remiza!")
        else:
            print("A câștigat " + final)
            current_state.game_table.draw_grid(marked_player=final)
        return True
    return False


# Se deschide pentru load un file explorer
def prompt_file():
    top = tkinter.Tk()
    top.withdraw()
    file_name = tkinter.filedialog.askopenfilename(initialdir = path + "\\saves",parent=top)
    top.destroy()
    return file_name


# Se afiseaza butoanele de la inceput
def draw_options(display, tabla_curenta):
    btn_alg = GrupButoane(
        top=30,
        left=30,
        buttons_list=[
            Button(display=display, w=80, h=40, text="Minmax", value="minmax"),
            Button(display=display, w=80, h=40, text="Alphabeta", value="alphabeta")
        ],
        selected_index=0)

    btn_juc = GrupButoane(
        top=100,
        left=30,
        buttons_list=[
            Button(display=display, w=60, h=40, text="Negru", value="n"),
            Button(display=display, w=60, h=40, text="Alb", value="a")
        ],
        selected_index=0)

    btn_jc = GrupButoane(
        top=170,
        left=30,
        buttons_list=[
            Button(display=display, w=90, h=40, text="Juc v Bot", value="pve"),
            Button(display=display, w=90, h=40, text="Juc v Juc", value="pvp"),
            Button(display=display, w=90, h=40, text="Bot v Bot", value="eve")
        ],
        selected_index=0)

    btn_dif = GrupButoane(
        top=240,
        left=30,
        buttons_list=[
            Button(display=display, w=90, h=40, text="Incepător", value=INCEPATOR_DEPTH),
            Button(display=display, w=90, h=40, text="Mediu", value=MEDIU_DEPTH),
            Button(display=display, w=90, h=40, text="Avansat", value=AVANSAT_DEPTH),
        ],
        selected_index=0)

    load = Button(display=display, top=300, left=30, w=70, h=40, text="Load", background_color=(190, 0, 190))

    ok = Button(display=display, top=360, left=30, w=70, h=40, text="Start", background_color=(155, 0, 55), background_color_hover=(155, 0, 55))
    
    btn_alg.draw()
    btn_juc.draw()
    btn_dif.draw()
    btn_jc.draw()
    load.draw()
    ok.draw()
    file = None
    
    # Aici se analizeaza ce se intampla daca se apasa pe butoane
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                if load.select_by_coord(pos):
                    file = prompt_file()
                    display.fill((0, 0, 0))
                    tabla_curenta.draw_grid()
                    return btn_juc.get_value(), btn_alg.get_value(), btn_dif.get_value(), btn_jc.get_value(), file

                if not load.select_by_coord(pos) and not btn_jc.select_by_coord(pos) and not btn_alg.select_by_coord(pos
                    ) and not btn_juc.select_by_coord(pos) and not btn_dif.select_by_coord(pos) and ok.select_by_coord(pos):
                        display.fill((0, 0, 0))
                        tabla_curenta.draw_grid()
                        return btn_juc.get_value(), btn_alg.get_value(), btn_dif.get_value(), btn_jc.get_value(), file
        pygame.display.update()


def main():
    # Functia main
    pygame.init()
    pygame.display.set_caption("Entropia lui Carreno - Tiganus Alexandru")
    # dimensiunea ferestrei in pixeli
    w = 100
    ecran = pygame.display.set_mode(size=(Game.COLUMNS * (w + 1) - 1, Game.COLUMNS * (w + 1) - 1 + 50))
    Game.initialize(ecran, cell_size=w)

    # Initializare tabla
    current_table = Game()  # apelam constructorul
    print("Tabla initiala")
    print(str(current_table))

    Game.Player1, algorithm, depth, players, file = draw_options(ecran, current_table)

    # Se analizeaza cu cn vrea sa joace jucatorul, alb negru

    if Game.Player1 == 'a':
        Game.Player2 = 'n'
    else:
        Game.Player2 = 'a'
    
    # Se analizeaza daca e juc vs juc samd
    config = {}
    if players == 'pvp':
        config = {'a': 'player', 'n': 'player'}
    elif players == 'pve':
        config = {'a': 'player', 'n': 'computer'}
    else:
        config = {'a': 'computer1', 'n': 'computer2'}

    # Daca jucatorul vrea sa joace cu alb, se inverseaza rolurile
    if Game.Player2 == 'a':
        config['n'], config['a'] = config['a'], config['n']

    # Aici se salveaza starile prin care am trecut pentru undo
    states = []

    # De aici se reseteaza jocul
    def restartPoint():
        # Daca se loadeaza, loadam o stare
        try:
            if file:
                fin = open(file, "r")
                juc = fin.readline()[0]
                nodes = int(fin.readline()[:-1])
                dep = int(fin.readline()[:-1])
                estimate = int(fin.readline()[:-1])
                mat = fin.read()
                matrix = [[] for i in range(5)]
                i, j = 0, 0
                for symbol in mat:
                    matrix[j].append(symbol)
                    i += 1
                    if i % 5 == 0:
                        j += 1
                game = Game(matrix)
                current_state = State(game, juc, dep, estimate=estimate, nodes=nodes)    
            else:
                current_state = State(current_table, 'n', depth)
        except:
            print("Load failed!")
            current_state = State(current_table, 'n', depth)
        current_table.available_squares = None
        current_table.selected_square = None
        current_table.draw_grid()

        states.append(copy.deepcopy(current_state))

        # Se initializeaza clasa de scriere in consola
        game_write = Write()

        selected_square = None

        # Se incepe jocul efectiv, se asteapta pt evenimente pygame si se iau masuri in functie de ele
        while True:
            # Daca joaca 2 calculatoare, vrem sa putem iesi oricand din joc
            if players == 'eve':
                for event in pygame.event.get():
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        pos = pygame.mouse.get_pos()
                        if Game.end_game_button.select_by_coord(pos):
                            print(game_write.final())
                            pygame.quit()
                            sys.exit()
            
            # Daca nu se poate face miscare, dam skip la tura
            if not current_state.game_table.can_move(current_state.j_curent):
                current_state.j_curent = Game.opposite_player(current_state.j_curent)
            
            # Daca muta jucatorul uman
            if config[current_state.j_curent] == "player":
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

                    # Highlight la casute
                    if event.type == pygame.MOUSEMOTION:
                        pos = pygame.mouse.get_pos()  # coordonatele cursorului
                        for np in range(len(Game.grid_cells)):
                            if Game.grid_cells[np].collidepoint(pos):
                                current_state.game_table.draw_grid(marked_line=np // Game.COLUMNS,
                                                                marked_column=np % Game.COLUMNS)
                                break
                    if event.type == pygame.KEYDOWN:
                        # Restart
                        if event.key == pygame.K_r:
                            restartPoint()
                            pygame.quit()
                            sys.exit()

                        # Undo
                        if event.key == pygame.K_u:
                            if len(states) >= 3:
                                states.pop(-1)
                                states.pop(-1)
                                current_state = copy.deepcopy(states[-1])
                                if len(states) != 1:
                                    current_state.j_curent = Game.opposite_player(current_state.j_curent)
                                current_state.game_table.draw_grid()

                        # Save
                        if event.key == pygame.K_s:
                            pygame.quit()
                            nume = input("Dati nume fisierului: ")
                            current_state.write(nume)
                            sys.exit()

                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        pos = pygame.mouse.get_pos()

                        # Exit
                        if Game.end_game_button.select_by_coord(pos):
                            print(game_write.final())
                            pygame.quit()
                            sys.exit()
                            
                        # Restart
                        if Game.restart_game_button.select_by_coord(pos):
                            restartPoint()
                            pygame.quit()
                            sys.exit()

                        # Undo
                        if Game.undo_button.select_by_coord(pos):
                            if len(states) >= 3:
                                states.pop(-1)
                                states.pop(-1)
                                current_state = copy.deepcopy(states[-1])
                                if len(states) != 1:
                                    current_state.j_curent = Game.opposite_player(current_state.j_curent)
                                current_state.game_table.draw_grid()

                        # Daca se apasa pe piesa
                        for np in range(len(Game.grid_cells)):
                            if Game.grid_cells[np].collidepoint(pos):
                                line = np // Game.COLUMNS
                                column = np % Game.COLUMNS

                                found_valid = False
                                if selected_square is not None:
                                    # Daca piesa e valida
                                    valid_moves = current_state.game_table.piece_moves(selected_square[0],
                                                                                    selected_square[1],
                                                                                    current_state.j_curent)
                                    # Generam miscarile 
                                    current_state.game_table.draw_square(np, current_state.j_curent, valid_moves)
                                    found_valid = False

                                    for valid_move in valid_moves:
                                        # Daca miscarea e valida
                                        if (line, column) == valid_move[1]:
                                            current_state.game_table = valid_move[0]
                                            found_valid = True
                                            break

                                # Asta inseamna ca se apasa pe piesa nu ca sa se miste ci ca sa fie selectata
                                if not found_valid and current_state.game_table.matrix[line][
                                    column] == current_state.j_curent:
                                    selected_square = (line, column)
                                    valid_moves = current_state.game_table.piece_moves(selected_square[0],
                                                                                    selected_square[1],
                                                                                    current_state.j_curent)
                                    current_state.game_table.draw_square(np, current_state.j_curent, valid_moves)

                                # Daca se face o miscare
                                if found_valid:
                                    # Afisam noua tabla
                                    current_state.game_table.draw_grid()

                                    # Afisam timpul de gandire, scorul si noua tabla
                                    game_write.update_current_state(current_state, "utilizator")
                                    game_write.update_moves(current_state)

                                    if show_if_final(current_state):
                                        break
                                    selected_square = None

                                    # Se baga starea in lista starilor de pana acum
                                    states.append(copy.deepcopy(current_state))

                                    # S-a realizat o move. Schimb jucatorul cu cel opus
                                    current_state.j_curent = Game.opposite_player(current_state.j_curent)

            else:
                # Mutare calculator
                # Analizam ce calculare scor folosim
                if config[current_state.j_curent] == "computer1":
                    score = '1'
                else:
                    score = '2'

                # Vedem ce algoritm e ales si facem in consecinta
                if algorithm == "minmax":
                    stare_actualizata = min_max(current_state, score)
                else:
                    stare_actualizata = alpha_beta(-500, 500, current_state, score)

                # Aici se face de fapt mutarea
                current_state.game_table = stare_actualizata.chosen_state.game_table
                current_state.game_table.draw_grid()

                # Afisam timpul de gandire, scorul si noua tabla
                game_write.update_nodes(stare_actualizata.nodes)
                game_write.update_current_state(current_state, "calculator")
                game_write.update_moves(current_state)

                if show_if_final(current_state):
                    break
                
                # Se baga starea in lista starilor de pana acum
                states.append(copy.deepcopy(current_state))

                # S-a realizat o move. Schimb jucătorul cu cel opus
                current_state.j_curent = Game.opposite_player(current_state.j_curent)

        print(game_write.final())
        
    restartPoint()

if __name__ == "__main__":
    main()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()