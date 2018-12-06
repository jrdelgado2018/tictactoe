# Much of the following header files were taken from Finance
import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

# I found the randint function on a StackOverflow forum
from random import randint

# Here are the functions that I wrote
# login_required and apology were taken from the distribution code to Finance
from helpers import userwin, cpuwin, move, randomspot, findwin, login_required, apology

# Configure application - from Finance
app = Flask(__name__)

# Reload templates when they are changed - from Finance
app.config["TEMPLATES_AUTO_RELOAD"] = True


# From Finance
@app.after_request
def after_request(response):
    """Disable caching"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies) - from Finance
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database - from Finance
db = SQL("sqlite:///tictactoe.db")


# I decided to represent the board as an lists with three lists as entries. Each sub-list represents one row of the board.
# A 0 means that the space isn't taken, a 1 means that the user took that space, and a -1 means that the computer took that space.
# Likewise, rows contains X's (for user spaces), O's (for computer spaces), and spaces (for empty spaces).
# Why spaces instead of empty characters? This comes in later with a script that I have running server-side.
board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
rows = [[" ", " ", " "], [" ", " ", " "], [" ", " ", " "]]

# I decided to store the option to defer the first move, as well as the difficulty, as lists with one entry.
# This was convenient for a jinja feature that I used, and also allowed me to alter them without having to declare global each time.
option = ["Let CPU Go First"]
difficulty = [""]


@app.route("/", methods=["GET"])
@login_required
def get_index():
    # When the index is called, the game resets. Each element of the board/rows is reset, and the defer option is reloaded. The difficulty is remembered.
    for i in range(3):
        for j in range(3):
            board[i][j] = 0
            rows[i][j] = " "
    option.clear()
    option.append("Let CPU Go First")
    return redirect("/game")


@app.route("/game", methods=["GET", "POST"])
@login_required
def game():
    # When the game is called with GET, it displays the game HTML template, passing in various jinja features.
    if request.method == "GET":
        return render_template("game.html", rows=rows, option=option, difficulty=difficulty[0], message="Your Turn!")

    # Else, if game is called with POST, the computer processes the user's move and then makes its move.
    else:
        # This counts the total number of moves made so far.
        moves = 0
        for i in range(3):
            for j in range(3):
                moves += abs(board[i][j])

        # If no moves have been made (so it was the user's first move), the defer option is removed.
        if moves == 0:
            option.remove("Let CPU Go First")

        # If the user defered his/her move, we move on without doing anything.
        if request.form.get("space") == "Let CPU Go First":
            # I found pass on a StackExchange forum
            pass
        # Else, we count the user's move and increment the moves counter. We first get the id of the button the user clicked.
        # The first digit of the id is the row number, and the second digit is the column number (both 0-indexed).
        # Then, we fill in that space with a 1 in the board list and an X in the rows list.
        else:
            space = int(request.form.get("space"))
            row = space // 10
            column = space % 10
            moves += 1
            board[row][column] = 1
            rows[row][column] = "X"

        # Next, we check if the user won the game on that move
        if userwin(board) == 1:
            # Any not-taken space in rows is converted to an empty character so that a button no longer shows up (this looks nicer).
            for i in range(3):
                for j in range(3):
                    if board[i][j] == 0:
                        rows[i][j] = ""
            # The result of this game is added into the history database.
            db.execute("INSERT INTO history (id, difficulty, result) VALUES(:ident, :diff, :result)",
                       ident=session["user_id"], diff=difficulty[0], result="Win")
            # The game board is returned, with the message altered to reflect the user win.
            return render_template("game.html", rows=rows, option=option, difficulty=difficulty[0], message="You Won!")

        # Next, we check if the game is a draw (so there have been nine total moves).
        if moves == 9:
            # The result of the game is added into the history database.
            db.execute("INSERT INTO history (id, difficulty, result) VALUES(:ident, :diff, :result)",
                       ident=session["user_id"], diff=difficulty[0], result="Tie")
            # The game board is returned, with the message altered to reflect the tie game.
            return render_template("game.html", rows=rows, option=option, difficulty=difficulty[0], message="Tie Game!")

        # If no win or tie, the CPU makes its move.
        # The CPU picks a space, and puts a -1 in the board and an O in rows.
        if difficulty[0] == "Easy":
            # If the difficulty is easy, the computer will move randomly half the time.
            x = randint(1, 2)
            if x == 1:
                y = randomspot(board)
                board[y[0]][y[1]] = -1
                rows[y[0]][y[1]] = "O"
            else:
                y = move(board, moves)
                board[y[0]][y[1]] = -1
                rows[y[0]][y[1]] = "O"
        elif difficulty[0] == "Medium":
            # If the difficulty is medium, the computer will move randomly one quarter of the time.
            x = randint(1, 4)
            if x == 1:
                y = randomspot(board)
                board[y[0]][y[1]] = -1
                rows[y[0]][y[1]] = "O"
            else:
                y = move(board, moves)
                board[y[0]][y[1]] = -1
                rows[y[0]][y[1]] = "O"
        else:
            # Else, the difficulty is hard, and the computer will never make a mistake.
            x = move(board, moves)
            board[x[0]][x[1]] = -1
            rows[x[0]][x[1]] = "O"
        # After the computer moved, the moves counter is incremented.
        moves += 1

        # Next, we check if the computer just won the game.
        if cpuwin(board) == -1:
            # Any not-taken space in rows is converted to an empty character so that a button no longer shows up (this looks nicer).
            for i in range(3):
                for j in range(3):
                    if board[i][j] == 0:
                        rows[i][j] = ""
            # The result of the game is inserted into the history database
            db.execute("INSERT INTO history (id, difficulty, result) VALUES(:ident, :diff, :result)",
                       ident=session["user_id"], diff=difficulty[0], result="Loss")
            # The game board is returned with a message that reflects the loss.
            return render_template("game.html", rows=rows, option=option, difficulty=difficulty[0], message="You Lost!")

        # Next, we check if the game was a tie (so nine moves have been made)
        if moves == 9:
            # The result of the game is insderted into the history database.
            db.execute("INSERT INTO history (id, difficulty, result) VALUES(:ident, :diff, :result)",
                       ident=session["user_id"], diff=difficulty[0], result="Tie")
            # The game board is returned with a message that reflects the tie.
            return render_template("game.html", rows=rows, option=option, difficulty=difficulty[0], message="Tie Game!")

        # Else, we reload the game to reflect the user's counted move and the CPU's move.
        return redirect("/game")


@app.route("/end", methods=["GET"])
def get_end():
    # Adapted from check in my solution to Finance
    """Return true if space in winning row/column/diagonal (or nobody won), else false, in JSON format"""

    # Get HTTP parameter with GET
    space = int(request.args.get("space"))

    # If nobody has won the game yet, we return true so that the space stays colored.
    if findwin(board) == None:
        return jsonify(True)
    else:
        # Else we find the winning row/column/diagonal.
        # If the space lies along that winning 3, we return true to allow it to stay colored. Else, we return false so it becomes black.
        x = findwin(board)
        if x[0] == "row":
            if space // 10 == x[1]:
                return jsonify(True)
            else:
                return jsonify(False)
        if x[0] == "column":
            if space % 10 == x[1]:
                return jsonify(True)
            else:
                return jsonify(False)
        if x[0] == "diagonal" and x[1] == 1:
            if space // 10 == space % 10:
                return jsonify(True)
            else:
                return jsonify(False)
        if x[0] == "diagonal" and x[1] == 2:
            if space % 10 == 2 - space // 10:
                return jsonify(True)
            else:
                return jsonify(False)


@app.route("/check", methods=["GET"])
def get_check():
    # This was taken from my submission to Finance.
    """Return true if username available, else false, in JSON format"""

    # Get HTTP parameter with GET
    username = request.args.get("username")

    # Query database for username
    rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)

    # See if the username is taken
    if len(rows) != 0 or len(str(username)) == 0:
        return jsonify(False)
    else:
        return jsonify(True)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # This was taken from the distribution code to Finance.

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/difficulty")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    # This was also taken from the distribution code to finance.

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # This was taken from my submission to Finance.

    # User reached route via GET (as by clicking a link or via redirect)
    if request.method == "GET":
        return render_template("register.html")

    # User reached route via POST (as by submitting a form via POST)
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted and confirmed
        elif not password:
            return apology("must provide password", 400)
        elif password != confirmation:
            return apology("passwords don't match", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=username)

        # Ensure username is not taken
        if len(rows) != 0:
            return apology("username taken", 400)

        # Insert user into users
        db.execute("INSERT into users (username, hash) VALUES(:username, :hashed)", username=username,
                   hashed=generate_password_hash(password, method='pbkdf2:sha256', salt_length=8))

        # Query database for username
        row = db.execute("SELECT * FROM users WHERE username = :username", username=username)

        # Remember which user has logged in
        session["user_id"] = row[0]["id"]

        # Redirect user to home page
        return redirect("/difficulty")


@app.route("/history", methods=["GET"])
@login_required
def get_history():
    """Show history of games"""
    # This was inspired by index in Finance.

    # Check that a game has been played so far
    rows = db.execute("SELECT * from history WHERE id = :ident", ident=session["user_id"])
    if not rows:
        return apology("no games yet")

    # Pass in the rows of the user's game history to jinja template
    return render_template("history.html", rows=rows)


@app.route("/difficulty", methods=["GET", "POST"])
@login_required
def change_difficulty():
    # If page reached from a GET request, displays the change difficulty page.
    if request.method == "GET":
        return render_template("difficulty.html")

    # Else, user (hopefully) chose a difficulty.
    else:
        difficulty[0] = request.form.get("difficulty")
        # I have a client-side script running to make sure a difficulty was selected, but just in case, I error-check.
        if not difficulty[0]:
            # If the user decides to be annoying and try to play the game without selecting the difficulty, it defaults to hard (in spite of him or her *evil laugh*).
            difficulty[0] = "Hard"
            return apology("please select a difficulty", 400)

        # Reloads the game with the selected difficulty.
        return redirect("/")