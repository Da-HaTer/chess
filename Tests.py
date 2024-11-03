import numpy as np
from board import State
from draw import Display
from utils import Logger


debug=True

start_board= np.array([
['','','','','','','B',''],
['','','','','','','',''],
['','','','','','','',''],
['','','','','','','',''],
['','','','','','','',''],
['','','','','','','',''],
['','','','','n','n','',''],
['','','','','k','','K','']])

board=np.ndarray((8,8),dtype=str)

#Loop

boundries=lambda i,j: 0<=i<8 and 0<=j<8
c2i=lambda c: (8-int(c[1]),ord(c[0])-97)
i2c=lambda i,j: chr(j+97)+str(8-i)
def mat(d:dict)->str:
    """
    Convert matieral count dictionary to string (for insufficient material check)"""
    return ' '.join([str(v)+k for k,v in d.items()])

def can_move(board:State,frm:tuple[int,int],to:tuple[int,int],ep=None,promote=None)->State:
    """Check if a move is legal (doesn't walk into check, stay in check or capture own pieces) , doesn't check for invalid moves (format ) """
    log=Logger(False).log

    log("Move: ",i2c(*to))
    friendlies = ('b','p','n','r','q','k') if board.white else ('B','P','N','R','Q','K')
    if board[to] in friendlies:
        return False
    
    new_pos=np.copy(board[:])
    new_pos[to]= promote if promote else new_pos[frm]
    new_pos[frm]=''
    kingpos=board.kings_pos[0:2] if board.white else board.kings_pos[2:]
    if ep: #Position of the en passant pawn to be capture 
        new_pos[ep]=''
    new_state=State(new_pos,board.white,board.castle,'-',board.halfmove_count,board.fullmove_count+1,board.kings_pos)#white kept to check if check persists
    if frm==kingpos:
        if board.white:
            new_state.kings_pos=to+board.kings_pos[2:]
        else:
            new_state.kings_pos=board.kings_pos[:2]+to


    if check(new_state):
        log("Can't move into check: ",i2c(*to))
        return None
    new_state.white=not new_state.white
    return new_state

def Flags(board:State,prev_states:dict[str]=None): #check for checkmate, stalemate and insufficient material returns flag and coordinates if needed
    """ loops on the board to check for stalemante , insufficient materials
        Returns flag if in terminal state
    """

    log=Logger(False).log
    bp=('B','P','N','R','Q') # black pieces
    wp=('b','p','n','r','q') # white pieces
    w_d=dict()
    b_d=dict()
    stalemate=True
    check_=check(board)
    pieces= ['b','p','n','r','q','k'] if board.white else ['B','P','N','R','Q','K']
    if check_:
        if checkmate(board):
            return("Checkmate")
    if board.halfmove_count==100:
        return("50-move Draw")

    for i in range(8):
        for j in range(8):
            #Update material dictionary (for material count)
            if board[i,j] in wp:
                if board[i,j] not in w_d:
                    w_d[board[i,j]]=1
                else:
                    w_d[board[i,j]]+=1
            elif board[i,j] in bp:
                if board[i,j] not in b_d:
                    b_d[board[i,j]]=1
                else:
                    b_d[board[i,j]]+=1
            
            #check for check & checkmate:
            if stalemate and board[i,j] in pieces : # check for stalemate
                pos=i,j
                moves=piece_moves(board,pos,early_exit=True)
                if moves: 
                    log("moves: ",moves)
                    stalemate=False

    if stalemate:
        return("Stalemate")
    
    mat_w,mat_b=mat(w_d),mat(b_d)
    insufficient_material= mat_w in ('','1b','1n','2n') and mat_b in ('','1B','1N','2N')
    if insufficient_material:
        return("Insufficient material")
    return 'Check' if check_ else None

def rook_casteling(pos:tuple[int,int],casteling:str)->str:
    """returns the new castelling string after a rook moves, gets captured"""
    i,j=pos
    s=casteling
    if (i,j)==(0,0):
        s=s.replace('q','')
    elif (i,j)==(0,7):
        s=s.replace('k','')
    elif (i,j)==(7,0):
        s=s.replace('Q','')
    elif (i,j)==(7,7):
        s=s.replace('K','')
    return s if s else '-'

def Pawn_DFS(board:State,pos:tuple[int,int],early_exit=False)->list[tuple[tuple[int,int,int,int],State]]:
        """ Returns all possible valid moves of a pawn on the board
        """
        white=board.white
        i,j=pos
        friends,foes=('b','p','n','r','q','k'),('B','P','N','R','Q','K')
        promotion=('Q','R','B','N') if not white else ('q','r','b','n')
        friends,foes=(friends,foes) if white else (foes,friends)
        ep=c2i(board.en_passant) if board.en_passant!="-" else None# en passant pawn coordinates
        found=[]
        row=4 if board.white else 3
        direction=1 if not white else -1
        if boundries(i+direction,j) and board[i+direction,j]=="": # simple move
            if i+direction in (0,7): #promotion
                for piece in promotion:
                    new_state=can_move(board,pos,(i+direction,j),None,piece)
                    if new_state:
                        if early_exit:
                            return True
                        new_state.en_passant='-'
                        new_state.halfmove_count=0
                        found.append(((i,j,i+direction,j),new_state))
            else:
                new_state=can_move(board,pos,(i+direction,j))
                if new_state:
                    if early_exit:
                        return True
                    new_state.en_passant='-'
                    new_state.halfmove_count=0
                    found.append(((i,j,i+direction,j),new_state))
        if boundries(i+2*direction,j) and board[i+2*direction,j]=="" and board[i+direction,j]=="" and i+2*direction==row: # simple 2 square move
            new_state=can_move(board,pos,(i+2*direction,j))
            if new_state:
                if early_exit:
                    return True
                new_state.en_passant=i2c(i+direction,j)
                new_state.halfmove_count=0
                found.append(((i,j,i+2*direction,j),new_state))
        for k in (-1,1): #diagonal capture 
            if boundries(i+direction,j+k) and board[i+direction,j+k] in foes:#diagonal capture
                if i+direction in (0,7): #promotion
                    for piece in promotion:
                        new_state=can_move(board,pos,(i+direction,j+k),None,piece)
                        if new_state:
                            if early_exit:
                                return True
                            new_state[i+direction,j+k]=piece
                            new_state.en_passant='-'
                            new_state.halfmove_count=0
                            found.append(((i,j,i+direction,j+k),new_state))
                else:
                    new_state=can_move(board,pos,(i+direction,j+k))
                    if new_state:
                        if early_exit:
                            return True
                        if board[i+direction,j+k].lower()=='r': #rook captured
                            new_state.castle=rook_casteling((i+direction,j+k),new_state.castle)# no longer can castle
                        new_state.en_passant='-'
                        new_state.halfmove_count=0
                        found.append(((i,j,i+direction,j+k),new_state))

        for c in (-1,1): # en passant
            if ep and boundries(i+direction,j+c) and (i+direction,j+c)==ep and ep[0]%2!=board.white:
                new_state= can_move(board,pos,(i+direction,j+c),ep=(i,j+c))
                if new_state:
                    if early_exit:
                        return True
                    new_state.en_passant='-'
                    new_state.halfmove_count=0
                    found.append(((i,j,i+direction,j+c),new_state))
    #### TO BE TESTED
        return found #return all possible moves (squares)
    
def Ranged_DFS(board:State,pos:tuple[int,int],early_exit=False)->list[tuple[tuple[int,int,int,int],State]]:
    """Returns all possible moves of a ranged piece on the board
    Rook, Bishop, Queen
    """

    log=Logger(False).log

    i,j=pos
    piece=board[i,j]
    if piece.lower()=='r':
        moves_kernel=[(0,1),(1,0),(0,-1),(-1,0)]
    elif piece.lower()=='b':
        moves_kernel=[(1,1),(-1,-1),(1,-1),(-1,1)]
    elif piece.lower()=='q':
        moves_kernel=[(0,1),(1,0),(0,-1),(-1,0),(1,1),(-1,-1),(1,-1),(-1,1)]

    friends,foes=('b','p','n','r','q','k'),('B','P','N','R','Q','K')
    friends,foes=(friends,foes) if board.white else (foes,friends)
    found=[]
    for move in moves_kernel: # for direction
        for k in range(1,8): 
            if 0<=i+k*move[0]<8 and 0<=j+k*move[1]<8: #within bounds
                log("Ranged DFS 1")
                square=board[i+k*move[0],j+k*move[1]]
                if square in friends:
                    break # next direction
                elif square in foes or square =="": #can move or capture
                    log("Ranged DFS 2")
                    new_state=can_move(board,pos,(i+k*move[0],j+k*move[1]))
                    if new_state:
                        log("Ranged DFS 3")
                        if piece.lower()=='r':#rook moves
                            new_state.castle=rook_casteling(pos,new_state.castle) # no longer can castle
                        if board[i+k*move[0],j+k*move[1]].lower()=='r': #opponent's rook captured
                            new_state.castle=rook_casteling((i+k*move[0],j+k*move[1]),new_state.castle)# opponent no longer can castle
                        log("Ranged DFS can move",i2c(*pos),i2c(i+k*move[0],j+k*move[1]))
                        if early_exit:
                            return True
                        new_state.en_passant='-'
                        if square in foes: # capture 
                            new_state.halfmove_count=0
                        found.append(((i,j,i+k*move[0],j+k*move[1]),new_state))
                    if square in foes:
                        break
                    else:
                        continue
            else:
                break # out of bounds search next direction

    return found

def Instant_DFS(board:State,pos:tuple[int,int],early_exit=False)->list[tuple[tuple[int,int,int,int],State]]:
    """Returns all possible moves of an instant piece on the board
    Knight, King
    """
    log=Logger(False).log
    i,j=pos
    piece=board[i,j]
    if piece.lower()=='n':
        moves_kernel=[(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]
    elif piece.lower()=='k':
        moves_kernel=[(0,1),(1,0),(0,-1),(-1,0),(1,1),(-1,-1),(1,-1),(-1,1)]
        kp=board.kings_pos
        casteling_symbols=('K','Q') if board.white else ('k','q')

    friends,foes=('b','p','n','r','q','k'),('B','P','N','R','Q','K')
    friends,foes=(friends,foes) if board.white else (foes,friends)
    found=[]
    for move in moves_kernel: # for direction
        if 0<=i+move[0]<8 and 0<=j+move[1]<8: #within bounds
            square=board[i+move[0],j+move[1]]
            if square in friends:
                continue # next direction
            elif square in foes or square =="": #can move or capture
                new_state=can_move(board,pos,(i+move[0],j+move[1]))
                
                if new_state:
                    
                    if early_exit:
                        return True
                    if square in foes:
                        new_state.halfmove_count=0
                    if board[i+move[0],j+move[1]].lower()=='r': #rook captured
                            new_state.castle=rook_casteling((i+move[0],j+move[1]),new_state.castle)# no longer can castle
                    if piece.lower()=='k':
                        new_state.kings_pos= (i+move[0],j+move[1])+kp[2:] if board.white else kp[:2]+(i+move[0],j+move[1]) #update king position
                        for symbol in casteling_symbols:
                            new_state.castle=new_state.castle.replace(symbol,'') #no longer can castle
                        new_state.castle='-' if not new_state.castle else new_state.castle
                    found.append(((i,j,i+move[0],j+move[1]),new_state))
    ##king casteling
    if piece.lower()=='k' and board.castle!='-' and not check(board): #can castle
        log(f"should castle {board} {pos}")
        if board.white:
            if 'K' in board.castle and np.array_equal(board[7, 5:7], np.array(['', ''])):  # clear path
                if can_move(board, pos, (7, 5)):  # not passing through check
                    new_state = can_move(board, pos, (7, 6))
                    if new_state:
                        new_state[7, 5] = 'r'
                        new_state[7, 7] = ''
                        new_state.castle = board.castle.replace('K', '').replace('Q', '')
                        new_state.kings_pos = (7, 6) + kp[2:]
                        new_state.en_passant = '-'
                        log("King casteling")
                        found.append(((7,4,7,6), new_state))
            if 'Q' in board.castle and np.array_equal(board[7, 1:4], np.array(['', '', ''])):  # clear path
                if can_move(board, pos, (7, 3)):  # not passing through check
                    new_state = can_move(board, pos, (7, 2))
                    if new_state:
                        new_state[7, 3] = 'r'
                        new_state[7, 0] = ''
                        new_state.castle = board.castle.replace('K', '').replace('Q', '')
                        new_state.kings_pos = (7, 2) + kp[2:]
                        new_state.en_passant = '-'
                        log("King casteling")
                        found.append(((7,4,7,2), new_state))
        else:
            if 'k' in board.castle and np.array_equal(board[0, 5:7], np.array(['', ''])):  # clear path
                if can_move(board, pos, (0, 5)):  # not passing through check
                    new_state = can_move(board, pos, (0, 6))
                    if new_state:
                        new_state[0, 5] = 'R'
                        new_state[0, 7] = ''
                        new_state.castle = board.castle.replace('k', '').replace('q', '')
                        new_state.kings_pos = kp[:2] + (0, 6)
                        new_state.en_passant = '-'
                        log("King casteling")
                        found.append(((0,4,0,6), new_state))
            if 'q' in board.castle and np.array_equal(board[0, 1:4], np.array(['', '', ''])):  # clear path
                if can_move(board, pos, (0, 3)):  # not passing through check
                    new_state = can_move(board, pos, (0, 2))
                    if new_state:
                        new_state[0, 3] = 'R'
                        new_state[0, 0] = ''
                        new_state.castle = board.castle.replace('k', '').replace('q', '')
                        new_state.kings_pos = kp[:2] + (0, 2)
                        new_state.en_passant = '-'
                        log("King casteling")
                        found.append(((0,4,0,2), new_state))
    return found
   
def piece_moves(board:State,pos:tuple[int,int],early_exit:bool=False)->list[tuple[tuple[int,int,int,int],State]]:
    """Returns all possible moves of a piece on the board and their corresponding new states
        use early_exit to check if a piece can make at least one move
    """
    log=Logger(False).log
    i,j=pos
    piece=board[i,j]
    moves=None
    if piece.lower() == 'p':
        log("Pawn DFS")
        moves=Pawn_DFS(board,pos,early_exit)
    elif piece.lower() in ('r','q','b'):
        log("Ranged DFS",piece)
        moves=Ranged_DFS(board,pos,early_exit)
    elif piece.lower() in ('n','k'):
        log("Instant DFS")
        moves=Instant_DFS(board,pos,early_exit)
    return moves

def all_moves(board:State)->list[tuple[tuple[int, int, int, int], State]]:
    """Returns all possible moves of this state
    format: fromi,fromj,toi,toj,new_state
    """
    moves=[]
    for i in range(8):
        for j in range(8):
            if (board.white and board[i,j] in ('b','p','n','r','q','k')) or (not board.white and board[i,j] in ('B','P','N','R','Q','K')):
                moves+=piece_moves(board,(i,j))
                    # print("move: ",move)
                    # print("st: ",st)
                    # print(f"from {i2c(i,j)} to {i2c(*move)}")
                    # new_state=State(board[:].copy(),not board.white,board.castle,board.en_passant,board.halfmove_count,board.fullmove_count+1,board.kings_pos)
                    # new_state[i,j]=''
                    # new_state[move]=board[i,j]
    return moves

def reverse_Ranged_DFS(board:State,pos:tuple[int,int],early_exit:bool=False)->list[any]:
    """searches for ranged pieces that can attack the given position
    """
    log=Logger(False).log

    found=[]
    bishop_kernel=[(1,1),(-1,-1),(1,-1),(-1,1)]
    rook_kernel=[(0,1),(1,0),(0,-1),(-1,0)]

    bishop_attackers=('B','Q') if board.white else ('b','q')
    rook_attackers=('R','Q') if board.white else ('r','q')
    friendlies=('b','p','n','r','q','k') if board.white else ('B','P','N','R','Q','K')
    
    for kernel in (rook_kernel,bishop_kernel):
        attackers=rook_attackers if kernel==rook_kernel else bishop_attackers
        for move in kernel:
            for k in range(1,8):
                i,j=pos[0]+k*move[0],pos[1]+k*move[1]
                if boundries(i,j):
                    square=board[i,j]
                    if square =='':
                        continue
                    if square in attackers:
                        log("Ranged DFS ATTACKER",i2c(i,j))
                        if early_exit:
                            return True
                        found.append((i,j))
                    else:
                        break
                else:
                    break
    return [square for square in found]
            
def reverse_Instant_DFS(board:State,pos:tuple[int,int],early_exit:bool=False,king:bool=True)->list[any]:
    """searches for instant pieces that can attack the given position
    """
    log=Logger(False).log
    log("DFS square: ",i2c(*pos))
    log("white: ",board.white)
    found=[]
    knight_kernel=[(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]
    king_kernel=[(0,1),(1,0),(0,-1),(-1,0),(1,1),(-1,-1),(1,-1),(-1,1)]
    knight_attackers=('N',) if board.white else ('n',)
    king_attackers=('K',) if board.white else ('k',)
    king_attackers=king_attackers if king else tuple()
    friendlies=('b','p','n','r','q','k') if board.white else ('B','P','N','R','Q','K')
    for kernel in (knight_kernel,king_kernel):
        attackers=knight_attackers if kernel==knight_kernel else king_attackers
        for move in kernel:
            i,j=pos[0]+move[0],pos[1]+move[1]
            if boundries(i,j):
                square=board[i,j]
                if square in attackers:
                    log("Instant DFS ATTACKER",i2c(i,j))
                    if early_exit:
                        return True
                    found.append((i,j))

    return [square for square in found]

def reverse_Pawn_DFS(board:State,pos:tuple[int,int],early_exit:bool=False)->list[any]:
    """searches for pawns that can attack the given position
    """
    log=Logger(False).log

    ### Test with en passant position
    ### fix pinned pawn cannot take to save checkmate
    found=[]
    i,j=pos
    attacker='P' if board.white else 'p'
    double_row=4 if board.white else 3
    direction=-1 if board.white else 1
    friendlies=('b','p','n','r','q','k') if board.white else ('B','P','N','R','Q','K')
    en_passant=c2i(board.en_passant) if board.en_passant!="-" else None
    if board.board[i,j] in friendlies: #capture
        for k in (-1,1): #diagonal capture 
            if boundries(i+direction,j+k): #diagonal capture
                square=board[i+direction,j+k]
                if square ==attacker:
                    log("Pawn DFS ATTACKER",i2c(i+direction,j+k))
                    if early_exit:
                        return True
                    found.append((i+direction,j+k))
            elif en_passant and boundries(i,j+k) and board[i,j+k]==attacker and en_passant==(i,j+k):
                log("Pawn DFS ATTACKER 2",i2c(i,j+k))
                if early_exit:
                    return True
                found.append((i,j+k))
    else: #advance move
        log("Pawn DFS")
        if board.board[pos]=='' and boundries(i+direction,j) and board[i+direction,j]==attacker:
            log("Pawn DFS ATTACKER 3",i2c(i+direction,j))
            if early_exit:
                return True
            found.append((i+direction,j))
        if board.board[pos]==''and board.board[i,j+direction]=='' and i==double_row and boundries(i+2*direction,j) and board[i+2*direction,j]==attacker:
            log("Pawn DFS ATTACKER 4",i2c(i+2*direction,j))
            if early_exit:
                return True
            found.append((i+2*direction,j))

    return [square for square in found]


def move_candidates(board:State,pos:tuple[int,int],early_exit:bool=False,king:bool=True)->list[any]:
    """Returns all possible pieces that can move to pos (current player's pieces)
        use early_exit if you want to check if at least one piece can move to pos
    """

    log = Logger(False).log
    
    i,j=pos
    moves=[]
    St=State(board[:],not board.white,board.castle,board.en_passant,board.halfmove_count,board.fullmove_count,board.kings_pos)
    #change turn to get friendly pieces instead of attackers
    dfs=reverse_Instant_DFS(St,pos,early_exit=False,king=king)
    for move in dfs:
        if can_move(board,move,pos):
            if early_exit:
                return True
            moves.append(move)
    dfs=reverse_Ranged_DFS(St,pos)
    for move in dfs:
        if can_move(board,move,pos):
            if early_exit:
                return True
            moves.append(move)
    dfs=reverse_Pawn_DFS(St,pos) ### en passant problem ?
    for move in dfs:
        if can_move(board,move,pos):
            if early_exit:
                return True
            moves.append(move)
    return moves

def interpolate(start:tuple[int,int],end:tuple[int,int]) ->list[tuple[int,int]]:
    """Returns all squares between two points on the board (exclusive)
    """
    i,j=start
    k,l=end
    dy,dx=k-i,l-j
    if i==k: #horizontal
        rg=range(j+1,l) if dx>0 else range(j-1,l,-1)
        return[(i,m) for m in rg]
    elif j==l: #vertical
        rg=range(i+1,k) if dy>0 else range(i-1,k,-1)
        return [(m,j) for m in rg]
    elif dy==dx: #diagonal with solpe=1
        rg=range(1,abs(k-i)) 
        dir=1 if dy>0 else -1
        return [(i+m*dir,j+m*dir) for m in rg]
    
    elif dy==-dx: #diagonal with slope=-1
        rg=range(1,abs(k-i)) 
        dir=1 if dy>0 else -1
        return [(i+m*dir,j-m*dir) for m in rg]
    return []

def check(board:State)->bool:
    """Returns weether the current player's king is in check
    searches in all directions for enemy pieces
    """
    log=Logger(False).log

    i,j=board.kings_pos[0:2] if board.white else board.kings_pos[2:]
    if reverse_Instant_DFS(board,(i,j),early_exit=True): #if a knight is attacking the king ###also searches for kings (prevents illegal king moves)
        log("-check: Instant DFS")
        return True
    elif reverse_Ranged_DFS(board,(i,j),early_exit=True): #if a ranged piece is attacking the king
        log("-check: Ranged DFS")
        return True
    elif reverse_Pawn_DFS(board,(i,j),early_exit=True): #if a pawn is attacking the king
        log("-check: Pawn DFS")
        return True
    return False    

def checkmate(board:State)->bool:
    """Returns weether the current player's king is in checkmate
    """
    log=Logger(False).log
    if not check(board):
        return False
    
    i,j=board.kings_pos[0:2] if board.white else board.kings_pos[2:]
    king_kernel=[(0,1),(1,0),(0,-1),(-1,0),(1,1),(-1,-1),(1,-1),(-1,1)]
    for move in king_kernel:# can move out of check
        if boundries(i+move[0],j+move[1]) and can_move(board,(i,j),(i+move[0],j+move[1])):
            log(f"{'white' if board.white else 'black'} can move out of check")
            return False
    attackers=reverse_Ranged_DFS(board,(i,j))
    attackers=attackers+reverse_Instant_DFS(board,(i,j),king=True)
    if len(attackers)>2:#can't block 
        log("can't block")
        return True
    for attacker in attackers:
        log(i2c(*attacker))
        path=interpolate((i,j),attacker)+[attacker]
        for square in path:
            log("square:",i2c(*square))
            if move_candidates(board,square,early_exit=True,king=False):
                log("can block")
                return False
    return True
            
def stalemate(board:State)->bool:
    """Returns weether the current player's king is in stalemate
    """
    pieces= ['b','p','n','r','q','k'] if board.white else ['B','P','N','R','Q','K']
    if check(board):
        return False
    for i in range(8):
        for j in range(8):
            if board[i,j] in pieces:
                if piece_moves(board,(i,j),early_exit=True):
                    return False            
    return True

def Parse_Input(board_state:State,board_states:list[State],board_states_count:dict[str,int],pgn_moves:list[str]):
    """Parses the input from the user
    """
    if i < len(premoves):
        move=premoves[i]
        i+=1
    else:
        w='\033[1m'+"white"+'\033[0m' # bold repr
        if Gui:
            print(f'{ w if white else "black"} to play')
        # print("Kings pos:",f"{piece.i2c(kings[0])} {piece.i2c(kings[1])}")
        # print("Old Kings pos:",f"{piece.i2c(old_kings[0])} {piece.i2c(old_kings[1])}")
        # print("moves :",moves)

        ### potentially move to seperate input function 
        move=input("Enter move: ( [move]|Takeback|Skip|Reset|[Get/Set] FEN|[Get/Set] PGN )\n")
        ### set pgn: plays the moves and checks if valid else return error invalid pgn
    move=move.replace("+","") #remove check notation
    move=move.replace("#","") #remove checkmate notation
    if move.lower()=="exit":
        ###return type ?
        return False
    elif move.lower()=="resign":
        ###update pgn
        pass
    elif move.lower()=="back":
        if len(board_state)<=1:
            print("No moves to take back")
            return None
        # pos=old_pos
        # kings=old_kings
        # en_passant=old_en_passant
        # white=not white
        ### should set state to previous state without recheking for checkmate/stalemate/checks
        ### recalculate kingpos ?
        board_states.pop()
        pgn_moves.pop()
        try:
            board_states_count[str(board_state)]-=1
        except Exception as e:
            print(e)
    
    elif move.lower()=="skip":
        #for testing for now
        board_state.white=not board_state.white
    elif move.lower()=="reset":
        board_state=State()
        board_states=[str(board_state)]
        board_states_count={str(board_state):1}
        ### should return something else
        return None
    elif move.upper()=="GET FEN":
        print(board_state.get_fen())
        input("press any key to continue...")
        return None
    elif move.upper()=="SET FEN":
        fen=input("Enter FEN:\n")
        board_state.set_fen(fen)
        #reset previous moves
        board_states=[str(board_state)]
        board_states_count={str(board_state):1}
        return None
    elif move.upper()=="GET PGN":
        print(' '.join([str(i+1)+'. '+pgn_moves[i] for i in range(len(pgn_moves))]))
        input("press any key to continue...")
        return None
    
    try:
        if move[0] in 'abcdefgh':  
            t=piece.pawn_move2(white,pos,move,en_passant)
            position=t[0]
            en_passant=t[1]
            # i,j=piece.c2i(move[-2:])
            # piece.Pawn_Dfs(pos,i,j,white,en_passant[1] if white else en_passant[0])
        elif move[0].lower() == 'n':
            position=piece.knight_move(white,pos,move[1:])
        elif move[0] == 'B':
            position=piece.bishop_move(white,pos,move[1:])
        elif move[0].lower()=='r':
            position=piece.rook_move(white,pos,move[1:])
        elif move[0].lower()=='q':
            position=piece.queen_move(white,pos,move[1:])
        elif move[0].lower()=='k':
            king_move=piece.King_move(white,pos,move[1:])
            position=king_move[0]
            kings=[king_move[1],kings[1]] if white else [kings[0],king_move[1]] #update kings position (for optimization)
        
        elif move.lower() in ('o-o','o-o-o'):
            position=piece.Castle(pos,white,move)
        else:
            raise InvalidMoveError(move)
        checks=(piece.King_check(position,True),piece.King_check(position,False)) #check if king is in check
        if white and checks[0] or not white and checks[1]: 
            raise IllegalMoveError(f"\033[33m {move} \033[0m"+f"\n\033[31mKing is in check: {checks}\033[0m")
        
        # board=Display(position)
        old_pos=np.copy(pos)
        old_en_passant=en_passant[:]
        pos=position
        if move[0]!="B" or move[0] not in ("N","R","Q","K"):
            moves.append((move[0]+move[1:].lower()))
        else:
            moves.append((move[0].upper()+move[1:].lower()))
        white=not white
    # finally:
    #     pass
    except Exception as e:
        # print(f"Error: {e}")
        print(traceback.format_exc())
        print("fen :",State().matrix_to_fen(old_pos,False))
        input("press any key to continue...")
Gui=True
premoves,i=[],0
pgn_moves=[]
board_state=State()
if Gui:
    ui=Display(board_state)
board_states=[str(board_state)]
board_states_count={str(board_state):1}
game=True
while game:
    break
    # piece=Piece('w',start_board)
    # board=Display(pos) if gui else None
    flag=Flags(board_state)
    if flag=="Stalemate":
        if moves:
            moves[-1]=moves[-1]+" 1/2-1/2" if ("1/2-1/2" not in moves[-1]) else moves[-1]
        game=False
    elif flag=="Checkmate":
        if moves:
            if board_state.white:
                moves[-1]=moves[-1]+"# 0-1" if ("#" not in moves[-1]) else moves[-1]+" 0-1"
            else:
                moves[-1]=moves[-1]+"# 1-0" if ("#" not in moves[-1]) else moves[-1]+" 1-0"
        if Gui:
            checks=(True,False) if board_state.white else (False,True)
            ui.update_checks(checks)
        game=False
        ##update moves
        # checkmate=True
        # if moves:
        #     moves[-1]=moves[-1]+"#"
        # print('moves :',moves)
        ##print stuff
        # print("\033[31mCheckmate\033[0m")
        # print("FEN :",Board().matrix_to_fen(pos,True))
        # print("PGN :", Board().Moves_to_Pgn(moves))
        # break
    
    elif flag=="Check":
        if Gui:
            checks=(True,False) if board_state.white else (False,True)
            ui.update_checks(checks)
        if moves:
            moves[-1]=moves[-1]+"#" if moves[-1][-1]!="#" else moves[-1]

    # print("white checks:", checks[0], "Black checks: ",checks[1])
    # print("enpassant:",en_passant[0],en_passant[1])
    # sleep(1)


if __name__=="__main__":
    start_board=np.array([
        ['R','N','B','Q','K','B','N','R'],
        ['P','P','P','P','P','P','P','P'],
        ['','','','','','','',''],
        ['','','','','','','',''],
        ['','','','','','','',''],
        ['','','','','','','',''],
        ['p','p','p','p','p','p','p','p'],
        ['r','n','b','q','k','b','n','r']
    ])

    empty_board=np.array([
        ['','','','','K','','',''],
        ['','','','','','','',''],
        ['','','','r','','q','',''],
        ['','','','','','','',''],
        ['','','','','','','',''],
        ['','','','','','','',''],
        ['','','','','','','',''],
        ['','','','k','','','','']
        ])


def count_moves_dfs(state, depth, current_depth=0):
    if current_depth==depth:
        return 1
    count= 0
    for move in all_moves(state):
        count+=count_moves_dfs(move[1],depth,current_depth+1)
    return count

def predict_moves(board:State, n): #Tree Nodes search by depth- keyword: Perft Results
    s0 = board
    return count_moves_dfs(s0, n)

def get_perft_result(fen:str,depth:int)->int:
    board=State(empty_board)
    board.set_fen(fen)
    Display(board)
    return predict_moves(board,depth)

def Run_Tests():
    import time
    with open("perftsuite.epd",'r') as f:
        lines=f.readlines()
        for i,line in enumerate(lines):
            print(f'***Testcase [{i+1}/{len(lines)}]***')
            line=line.split(';')
            fen,testcases=line[0][:-1],line[1:]

            for j,test in enumerate(testcases):
                print(f'Depth [{j+1}/{len(testcases)}]')
                depth,result=test[:-1].split(' ')
                depth=int(depth[1:])
                result=int(result)
                if result>5e5:
                    break
                start=time.time()
                if get_perft_result(fen,depth)!=result:
                    print('Did not pass')
                    print(fen,depth,result)
                    break
                print("Passed")
                print(f"Time: {(time.time()-start):.3f}")
                print()

Run_Tests()
# print(get_perft_result("r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10 ",3))
exit()
