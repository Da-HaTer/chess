
import numpy as np
import re
class Board:
    start_board= np.array([
            ['R','N','B','Q','K','B','N','R'],
            ['P','P','P','P','P','P','P','P'],
            ['','','','','','','',''],
            ['','','','','','','',''],
            ['','','','','','','',''],
            ['','','','','','','',''],
            ['p','p','p','p','p','p','p','p'],
            ['r','n','b','q','k','b','n','r']
        ])
    def __init__(self,board:np.ndarray=None,white:bool=True,castle:str='-',en_passant:str='-',halfmove_count:int =0 ,fullmove_count:int =0):
        if board is None:
            self.board_position = self.start_board
        self.white=white
        self.castle=castle
        self.en_passant=en_passant
        self.halfmove_count=halfmove_count
        self.fullmove_count=fullmove_count
    
    def __eq__(self, board:object) -> bool:
        return self.board==board[:]
        
    def __getitem__(self,idx) -> np.ndarray:
        return self.board_position[idx]
    def __setitem__(self,idx:tuple[int,int],val: np.ndarray) -> None:
        self.board_position[idx]=val

    def setboard(self,board=start_board):
        self.board_position = board

    def get_fen(self) -> str:
        en_passant=self.en_passant if self.en_passant is not None else '-'
        castle=self.castle if self.castle is not None else '-'
        white="w" if self.white else "b"
        return self.__matrix_to_fen(self.board_position)+f" {white} {castle} {en_passant} {self.halfmove_count} {self.fullmove_count}"

    def __str__(self):
        return self.get_fen()

    def set_fen(self,fen:str) -> None:
        fen = fen.split(' ')
        self.white=fen[1]=='w'
        self.castle=fen[2]
        self.en_passant=fen[3]
        self.halfmove_count=fen[4]
        self.fullmove_count=fen[5]
        self.board_position=self.__fen_to_matrix(fen[0])
    
    def __fen_to_matrix(self,fen): #helper
        fen = fen.split(' ')[0]
        fen = fen.split('/')
        board = np.array([['']*8 for i in range(8)])
        for i in range(8):
            j = 0
            for k in fen[i]:
                if k.isdigit():
                    j += int(k)
                else:
                    board[i,j] = k
                    j += 1
        return board
    
    def __matrix_to_fen(self,matrix):
        fen = ''
        for i in range(8):
            j = 0
            for k in matrix[i]:
                if k == '':
                    j += 1
                else:
                    if j > 0:
                        fen += str(j)
                        j = 0
                    fen += k
            if j > 0:
                fen += str(j)
            if i < 7:
                fen += '/'
        return fen

    ### to be tested and moved to game, also extra game attributes like player time mode etc
    def pgn_to_moves(self,pgn): ### move to utils 
        pgn =re.sub(r'\{.*?\}\s', '', pgn) 
        pgn = pgn.split(' ')
        moves = []
        for i in pgn:
            if '.' in i:
                continue
            moves.append(i)
        return moves
    
    def Moves_to_Pgn(self,moves):
        s=""
        i=0
        while i<len(moves)-1:
            s+=str(i//2+1)+". "+moves[i]+" "+moves[i+1]+" "
            i+=2
        return s
    
    def randomize_board_dirty(self):
        #dirty randomization (no checks for valid or legal positions)
        arr=self.board_position
        arr = arr.flatten()
        np.random.shuffle(arr)
        arr = arr.reshape((8, 8))
        self.board_position=arr

if __name__=='__main__':
    ##TESTS
    board=Board()
    # fen test
    fen="q3kb1r/1p2pppp/5n2/2rp4/3Q1B2/4PN2/P1n2PPP/R3K2R w KQk - 0 14"
    # newboard=board.fen_to_matrix(fen)
    print(board.get_fen())
    print(board)
    board.set_fen("rn1qkb1r/p1p1pppp/1p3n2/3p1b2/2PP4/1Q3N2/PP2PPPP/RNB1KB1R b KQkq - 0 5")
    print(board)
    print(board[:])
    board[0,:]="a"
    print(board[:])

    # reset board tests
    board.setboard()
    board.randomize_board_dirty()
    print(board[:])
    # pgn test
    pgn="1. e4 e6 2. d4 d5 3. e5 c5 4. c3 cxd4 5. cxd4 Bb4+ 6. Nc3 Nc6 7. Nf3 Nge7 8. Bd3 O-O 9. Bxh7+ Kxh7 10. Ng5+ Kg6 11. h4 Nxd4 12. Qg4 f5 13. h5+ Kh6 14. Nxe6+ g5 15. hxg6# 1-0"
    print(board.pgn_to_moves(pgn))