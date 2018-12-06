# A StackExchange forum introduced me to the numpy library, which allows you to treat lists of lists as matricies
# I had to download this library from the web and upload it to the IDE
# The only function I use from numpy is transpose, which flips the rows and columns of the matrix
import numpy
# These are from Finance
import requests
import urllib.parse
from flask import redirect, render_template, request, session
from functools import wraps
# Once again, I found the random library on StackOverflow
from random import randint


# Returns 1 if the board indicates that the user won the game, else None
def userwin(board):
    # Check rows for a winning row
    for row in board:
        if row[0] + row[1] + row[2] == 3:
            return 1
    # Check columns for a winning column
    tboard = numpy.transpose(board)
    for row in tboard:
        if row[0] + row[1] + row[2] == 3:
            return 1
    # Check diagonals for winning diagonal
    if board[0][0] + board[1][1] + board[2][2] == 3 or board[0][2] + board[1][1] + board[2][0] == 3:
        return 1
    # Else, nobody won
    return None


# Returns -1 if the board indicates that the CPU won the game, else None
def cpuwin(board):
    # Check rows for CPU win
    for row in board:
        if row[0] + row[1] + row[2] == -3:
            return -1
    # Check columns for CPU win
    tboard = numpy.transpose(board)
    for row in tboard:
        if row[0] + row[1] + row[2] == -3:
            return -1
    # Check diagonals for CPU win
    if board[0][0] + board[1][1] + board[2][2] == -3 or board[0][2] + board[1][1] + board[2][0] == -3:
        return -1
    # Else, nobody won
    return None


# Checks if the CPU has two in a row, then if the user has two in a row
# Returns the coordinates of the empty space in that two in a row, else None if no two in a row
def check(board):
    tboard = numpy.transpose(board)
    # Check for CPU win first
    # Check rows for two in a row
    for i in range(3):
        if board[i][0] + board[i][1] + board[i][2] == -2 and board[i][0] * board[i][1] * board[i][2] == 0:
            for j in range(3):
                if board[i][j] == 0:
                    return [i, j]
    # Check columns for two in a row
    for i in range(3):
        if tboard[i][0] + tboard[i][1] + tboard[i][2] == -2 and tboard[i][0] * tboard[i][1] * tboard[i][2] == 0:
            for j in range(3):
                if tboard[i][j] == 0:
                    return [j, i]
    # Check diagonals for two in a row
    if board[0][0] + board[1][1] + board[2][2] == -2 and board[0][0] * board[1][1] * board[2][2] == 0:
        for i in range(3):
            if board[i][i] == 0:
                return [i, i]
    if board[0][2] + board[1][1] + board[2][0] == -2 and board[0][2] * board[1][1] * board[2][0] == 0:
        for i in range(3):
            if board[i][2-i] == 0:
                return [i, 2-i]
    # Now, check for user two in a row
    # Check rows for two in a row
    for i in range(3):
        if board[i][0] + board[i][1] + board[i][2] == 2 and board[i][0] * board[i][1] * board[i][2] == 0:
            for j in range(3):
                if board[i][j] == 0:
                    return [i, j]
    # Check columns for two in a row
    for i in range(3):
        if tboard[i][0] + tboard[i][1] + tboard[i][2] == 2 and tboard[i][0] * tboard[i][1] * tboard[i][2] == 0:
            for j in range(3):
                if tboard[i][j] == 0:
                    return [j, i]
    # Check diagonals for two in a row
    if board[0][0] + board[1][1] + board[2][2] == 2 and board[0][0] * board[1][1] * board[2][2] == 0:
        for i in range(3):
            if board[i][i] == 0:
                return [i, i]
    if board[0][2] + board[1][1] + board[2][0] == 2 and board[0][2] * board[1][1] * board[2][0] == 0:
        for i in range(3):
            if board[i][2-i] == 0:
                return [i, 2-i]
    # Else, nobody has two in a row
    return None


# Returns the optimal corner for the CPU to play given certain situations
def corners(board):
    # If the computer already has two corners, it should pick a third corner that 1. isn't taken and 2. opens up multiple pathways to win
    if board[0][0] + board[0][2] + board[2][0] + board[2][2] <= -1 and board[0][0] * board[0][2] * board[2][0] * board[2][2] == 0:
        if board[1][0] != 1 and board[0][0] == 0 and board[0][1] != 1:
            return [0, 0]
        elif board[0][1] != 1 and board[0][2] == 0 and board[1][2] != 1:
            return [0, 2]
        elif board[1][0] != 1 and board[2][0] == 0 and board[2][1] != 1:
            return [2, 0]
        elif board[2][1] != 1 and board[2][2] == 0 and board[1][2] != 1:
            return [2, 2]
        else:
            pass

    # Else, if the computer only has 1 corner, it should pick another corner that 1. isn't taken and 2. opens multiple potential winning pathways
    elif board[0][0] == -1 or board[2][2] == -1:
        if (board[1][0] == 1 or board[2][0] == 1 or board[2][1] == 1) and board[0][2] == 0:
            return [0, 2]
        elif board[2][0] == 0:
            return [2, 0]
        else:
            pass

    # Same as above, but with different corners
    elif board[0][2] == -1 or board[2][0] == -1:
        if (board[0][0] == 1 or board[0][1] == 1 or board[1][0] == 1) and board[2][2] == 0:
            return [2, 2]
        elif board[0][0] == 0:
            return [0, 0]
        else:
            pass

    # Else, if computer has no corners and the user has at least one corner, the computer should take the middle space if open
    elif (board[0][0] == 1 or board[2][0] == 1 or board[0][2] == 1 or board[2][2] == 1) and board[1][1] == 0:
        return [1, 1]

    # Else, if neither computer nor user has any corner, should pick the corner that is most open
    else:
        if board[1][0] != 1 and board[0][0] == 0 and board[0][1] != 1:
            return [0, 0]
        elif board[0][1] != 1 and board[0][2] == 0 and board[1][2] != 1:
            return [0, 2]
        elif board[1][0] != 1 and board[2][0] == 0 and board[2][1] != 1:
            return [2, 0]
        elif board[2][1] != 1 and board[2][2] == 0 and board[1][2] != 1:
            return [2, 2]
        # If no corners are really open, then it must be towards the end of the game, so we should pick any spot that's free
        else:
            return None


# Returns the coordinate of a random spot on the board that is unoccupied
def randomspot(board):
    # randint function found at https://pythonspot.com/random-numbers/
    while True:
        x = randint(0, 2)
        y = randint(0, 2)
        if board[x][y] == 0:
            return [x, y]


# Returns the coordinates of the best CPU move given some special-case behavior by the user at the beginning of the game
def specialuser(board):
    # If the computer has the middle space and the user tries to sandwich him with corners, the computer should take an edge
    # Also, if the computer has the middle and the user has a corner and an edge, the computer should take the corner touching the user's edge and in line with the user's corner
    if board[1][1] == -1:
        if board[0][0] == 1 and board[2][2] == 1:
            return [1, 0]
        elif board[0][2] == 1 and board[2][0] == 1:
            return [0, 1]
        elif board[0][0] == 1:
            if board[1][2] == 1:
                return [0, 2]
            elif board[2][1] == 1:
                return [2, 0]
        elif board[0][2] == 1:
            if board[1][0] == 1:
                return [0, 0]
            elif board[2][1] == 1:
                return [2, 2]
        elif board[2][0] == 1:
            if board[0][1] == 1:
                return [0, 0]
            elif board[1][2] == 1:
                return [2, 2]
        elif board[2][2] == 1:
            if board[1][0] == 1:
                return [2, 0]
            elif board[0][1] == 1:
                return [0, 2]
        else:
            pass
    # If none of those conditions are met, None is returned
    else:
        return None


# Returns the coordinates of a special case behavior by the CPU at the beginning of the game
def specialcpu(board):
    # If the user has the center and the computer has a corner, the computer should try to sandwich with the other corner
    if board[1][1] == 1:
        if board[0][0] == -1:
            return [2, 2]
        elif board[0][2] == -1:
            return [2, 0]
        elif board[2][0] == -1:
            return [0, 2]
        elif board[2][2] == -1:
            return [0, 0]
        else:
            pass
    # If that condition is not met, None is returned
    else:
        return None


# This returns the coordinates of the CPU's move for any given board
def move(board, moves):
    # Checks if someone has a two in a row, and takes the corresponding space if empty
    if check(board) != None:
        return check(board)

    # Next, checks if the two special cases apply, and takes that space
    elif moves == 3 and specialuser(board) != None:
        return specialuser(board)
    elif moves == 2 and specialcpu(board) != None:
        return specialcpu(board)

    # Next, picks the optimal corner to take
    elif corners(board) != None:
        return corners(board)

    # If none of those conditions apply, the optimal move is just to pick a random space because the game must be winding down
    else:
        return randomspot(board)


# Returns a list that defines the winning row/column/diagonal of a board (if applicable)
def findwin(board):
    tboard = numpy.transpose(board)

    # If the board indicates that the user won, iterates over rows, then columns, then diagonals until it finds the winning three in a row
    if userwin(board) == 1:
        for i in range(3):
            if board[i][0] + board[i][1] + board[i][2] == 3:
                return ["row", i]
        for i in range(3):
            if tboard[i][0] + tboard[i][1] + tboard[i][2] == 3:
                return ["column", i]
        if board[0][0] + board[1][1] + board[2][2] == 3:
            return ["diagonal", 1]
        if board[0][2] + board[1][1] + board[2][0] == 3:
            return ["diagonal", 2]

    # If the board indicates that the CPU won, iterates over rows, then columns, then diagonals until it finds the winning three in a row
    elif cpuwin(board) == -1:
        for i in range(3):
            if board[i][0] + board[i][1] + board[i][2] == -3:
                return ["row", i]
        for i in range(3):
            if tboard[i][0] + tboard[i][1] + tboard[i][2] == -3:
                return ["column", i]
        if board[0][0] + board[1][1] + board[2][2] == -3:
            return ["diagonal", 1]
        if board[0][2] + board[1][1] + board[2][0] == -3:
            return ["diagonal", 2]

    # If nobody has won yet, None is returned
    else:
        return None


# Taken from the starter code to Finance
def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


# Also taken from the starter code to Finance
def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code