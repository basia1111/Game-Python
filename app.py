import uuid

from flask import Flask, url_for
from flask import render_template
from flask import redirect
from flask import request
from flask import session, escape
import uuid

app = Flask(__name__)
app.secret_key = 'any random string'

games = {}
multiplayer_games = {}


class Ship:

    def __init__(self, name, fleet, sails):
        self.name = name
        self.fleet = fleet
        self.sails = sails
        self.status = 'down'
        self.direction = 'right'
        self.state = 'visible'
        self.defeated = None
        self.x = 0
        self.y = 0

    def change_status(self):
        self.status = 'up'

    def change_state(self, name):
        self.state = name

    def uncover(self):
        self.state = 'visible'

    def change_direction(self, direction):
        self.direction = direction

    def change_location(self, x, y):
        self.x = x
        self.y = y


def calculate_move(sails, direction, x, y):
    one = {
        'up': [(x - 1, y)],
        'down': [(x + 1, y)],
        'left': [(x, y - 1)],
        'right': [(x, y + 1)]
    }
    two = {
        'up': [(x - 1, y - 1), (x + 1, y - 1)],
        'down': [(x + 1, y - 1), (x + 1, y + 1)],
        'left': [(x - 1, y - 1), (x + 1, y - 1)],
        'right': [(x - 1, y + 1), (x + 1, y + 1)]
    }

    three = {
        'up': [(x - 1, y), (x - 1, y - 1), (x + 1, y - 1)],
        'down': [(x + 1, y), (x + 1, y - 1), (x + 1, y + 1)],
        'left': [(x, y - 1), (x - 1, y - 1), (x + 1, y - 1)],
        'right': [(x, y + 1), (x - 1, y + 1), (x + 1, y + 1)]
    }

    moves = {
        1: one,
        2: two,
        3: three
    }
    moves2 = moves[sails]

    return moves2[direction]


def move_on_board(moves, positions):
    checked_moves = list()
    for move in moves:
        if move in positions:
            checked_moves.append(move)
    return checked_moves


def empty_fields(positions, ships):
    fields = list()
    for position in positions:
        i = 0
        for ship in ships:
            if (ships[ship].x, ships[ship].y) == position:
                i = 1
        if i == 0:
            fields.append(position)

    return fields


def free_fields(moves, ships):
    free = list()
    for move in moves:
        i = 0
        for ship in ships:
            if (ships[ship].x, ships[ship].y) == move:
                i = 1
        if i == 0:
            free.append(move)

    return free


def turned_down_fields(moves, ships):
    turned_down = list()

    for ship in ships:
        if (ships[ship].x, ships[ship].y) in moves:
            if ships[ship].status == 'down':
                turned_down.append((ships[ship].x, ships[ship].y))
    return turned_down


def enemy_fields(moves, ships, fleet):
    enemy = list()
    for ship in ships:
        if ((ships[ship].x, ships[ship].y) in moves) and ships[ship].status == 'up':

            if ships[ship].fleet != fleet:
                enemy.append((ships[ship].x, ships[ship].y))
    return enemy


def search_for_covered(name, ships):
    for ship in ships:
        if (ships[ship].state == name):
            ships[ship].uncover()


class Player:
    def __init__(self, name, fleet, state, identity):
        self.name = name
        self.fleet = fleet
        self.defeated_ships = list()
        self.state = state
        self.identity = identity

    def add_ship(self, ship):
        self.defeated_ships.append(ship)

    def count_points(self):
        points = 0
        for ship in self.defeated_ships:
            points += games[session['key']].ships[ship].sails
        return points


class Game:

    def __init__(self, name_p, name_s, mode):
        self.players = list()
        self.mode = mode

        if self.mode == 'single':
            self.players.append(Player(name_p, 'p', 'active', 'human')),
            self.players.append(Player(name_s, 's', 'waiting', 'computer'))
        else:
            self.players.append(Player(name_p, 'p', 'active', 'human')),
            self.players.append(Player(name_s, 's', 'waiting', 'human'))
        self.active = 'p'

        self.ships = {
            'Dark_Howler': Ship('Dark_Howler', 'p', 1),
            'Deadly_Destiny': Ship('Deadly_Destiny', 'p', 1),
            'White_Shark': Ship('White_Shark', 's', 1),
            'Fish_Fryer': Ship('Fish_Fryer', 's', 1),
            'Revenge_Tide': Ship('Revenge_Tide', 'p', 2),
            'Bloody_Hangman': Ship('Bloody_Hangman', 'p', 2),
            'Santa_Maria': Ship('Santa_Maria', 's', 2),
            'Old_James': Ship('Old_James', 's', 2),
            'Jolly_Roger': Ship('Jolly_Roger', 'p', 3),
            'Black_Pearl': Ship('Black_Pearl', 'p', 3),
            'Florencia': Ship('Florencia', 's', 3),
            'Marco_Polo': Ship('Marco_Polo', 's', 3)

        }

        self.position = [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2)]
        import random
        random.shuffle(self.position)

        i = 0
        for ship in self.ships:
            self.ships[ship].change_location(self.position[i][0], self.position[i][1])
            i += 1

    def change_active(self, player):
        self.active = player


@app.route('/')
def home():  # put application's code here
    if session.get('key') is None:
        session['key'] = uuid.uuid4()
    return render_template('home.html')


def check():
    if session.get('key') and 'games' in globals():
        print('++++++')
        return True
    print('------')
    return False


@app.route('/rules')
def rules():
    return render_template('rules.html')


# HOT SEAT##############################################################################
@app.route('/hot_seat/form', methods=['GET', 'POST'])
def hot_seat_form():

    if request.method == 'POST':
        return hot_seat_players(request.form.get("name_p"), request.form.get("name_s"))

    return render_template('hot_seat/form.html')


def hot_seat_players(name_p, name_s):

    games[session['key']] = Game(name_p, name_s, 'hot_seat')

    return redirect(url_for('hot_seat_board'))


@app.route('/hot_seat/board', methods=['GET'])
def hot_seat_board():
    if session.get('key') not in games:
        return redirect('/', code=302)
    pirates = games[session['key']].players[0].count_points()
    spanish = games[session['key']].players[1].count_points()
    fields = empty_fields(games[session['key']].position, games[session['key']].ships)
    if pirates == 12 or spanish == 12:
        return render_template('hot_seat/end.html', game=games[session['key']], fields=fields,
                               player=games[session['key']].active, pirates=pirates,
                               spanish=spanish)

    return render_template('hot_seat/board.html', game=games[session['key']], fields=fields,
                           player=games[session['key']].active, pirates=pirates,
                           spanish=spanish)


@app.route('/hot_seat/board/move/<name>')
def hot_seat_move(name):
    if session.get('key') not in games:
        return redirect('/', code=302)
    if games[session['key']].ships[name].status == 'down':
        games[session['key']].ships[name].change_status()
        pirates = games[session['key']].players[0].count_points()
        spanish = games[session['key']].players[1].count_points()
        return redirect(url_for('hot_seat_rotate', name=name, pirates=pirates,
                                spanish=spanish))

    move = calculate_move(games[session['key']].ships[name].sails, games[session['key']].ships[name].direction,
                          games[session['key']].ships[name].x, games[session['key']].ships[name].y)
    moves = move_on_board(move, games[session['key']].position)

    free = free_fields(moves, games[session['key']].ships)
    turned = turned_down_fields(moves, games[session['key']].ships)
    enemy = enemy_fields(moves, games[session['key']].ships, games[session['key']].ships[name].fleet)
    pirates = games[session['key']].players[0].count_points()
    spanish = games[session['key']].players[1].count_points()

    fields = empty_fields(games[session['key']].position, games[session['key']].ships)
    return render_template('hot_seat/move.html', game=games[session['key']], free=free, name=name, fields=fields,
                           enemy=enemy,
                           turned=turned, pirates=pirates,
                           spanish=spanish, moves=moves)


@app.route('/hot_seat/board/move/turned/<ship1>/<ship2>')
def make_move_turned(ship1, ship2):
    if session.get('key') not in games:
        return redirect('/', code=302)
    a = (games[session['key']].ships[ship2].x, games[session['key']].ships[ship2].y)[:]
    if games[session['key']].ships[ship1].defeated:
        games[session['key']].ships[games[session['key']].ships[ship1].defeated].state = 'visible'

    games[session['key']].ships[ship1].change_location(a[0], a[1])
    games[session['key']].ships[ship1].defeated = games[session['key']].ships[ship2].name
    games[session['key']].ships[ship2].change_state(games[session['key']].ships[ship1].name)

    return change_player()


@app.route('/hot_seat/board/move/free/<ship1>/<pole>')
def make_move_free(ship1, pole):
    if session.get('key') not in games:
        return redirect('/', code=302)
    fields = empty_fields(games[session['key']].position, games[session['key']].ships)
    if games[session['key']].ships[ship1].defeated:
        games[session['key']].ships[games[session['key']].ships[ship1].defeated].state = 'visible'
    games[session['key']].ships[ship1].change_location(fields[int(pole)][0], fields[int(pole)][1])
    return change_player()


@app.route('/hot_seat/board/move/enemy/<ship1>/<ship2>')
def make_move_enemy(ship1, ship2):
    if session.get('key') not in games:
        return redirect('/', code=302)
    if games[session['key']].ships[ship1].defeated:
        games[session['key']].ships[games[session['key']].ships[ship1].defeated].state = 'visible'
        games[session['key']].ships[ship1].defeated = None
    a = (games[session['key']].ships[ship2].x, games[session['key']].ships[ship2].y)[:]
    games[session['key']].ships[ship1].change_location(a[0], a[1])
    games[session['key']].ships[ship2].change_location(0, 0)
    if games[session['key']].ships[ship2].defeated:
        games[session['key']].ships[ship1].defeated = games[session['key']].ships[ship2].defeated

    for player in games[session['key']].players:
        if player.fleet == games[session['key']].ships[ship1].fleet:
            player.add_ship(games[session['key']].ships[ship2].name)

    return change_player()


@app.route('/hot_seat/board/rotate/<name>')
def hot_seat_rotate(name):
    if session.get('key') not in games:
        return redirect('/', code=302)
    fields = empty_fields(games[session['key']].position, games[session['key']].ships)
    pirates = games[session['key']].players[0].count_points()
    spanish = games[session['key']].players[1].count_points()
    return render_template('hot_seat/rotate.html', name=name, game=games[session['key']], fields=fields,
                           pirates=pirates,
                           spanish=spanish)


@app.route('/hot_seat/board/rotate/<name>/<direction>')
def hot_seat_rotate_change(name, direction):
    if session.get('key') not in games:
        return redirect('/', code=302)
    games[session['key']].ships[name].change_direction(direction)
    return change_player()


@app.route('/change_player')
def change_player():
    if session.get('key') not in games:
        return redirect('/', code=302)
    d = {
        'waiting': 'active',
        'active': 'waiting'
    }
    for player in games[session['key']].players:
        player.state = d[player.state]
        if player.count_points() == 12:
            redirect(url_for('hot_seat_end', winner=player))

        else:
            if player.state == 'active':
                games[session['key']].change_active(str(player.fleet))

    return redirect(url_for('hot_seat_board'))


@app.route('/hot_seat/board/end/<winner>')
def hot_seat_end(winner):
    if session.get('key') not in games:
        return redirect('/', code=302)
    return render_template('hot_seat/rotate.html', game=games[session['key']], winner=winner)


################################################################################################
# SINGLE


@app.route('/solo/form', methods=['GET', 'POST'])
def solo_form():

    if request.method == 'POST':
        return solo_players(request.form.get("name_p"), request.form.get("name_s"))

    return render_template('solo/form.html')


def solo_players(name_p, name_s):

    games[session['key']] = Game(name_p, name_s, 'solo')

    return redirect(url_for('solo_board'))


@app.route('/solo/board', methods=['GET'])
def solo_board():
    if session.get('key') not in games:
        return redirect('/', code=302)
    pirates = games[session['key']].players[0].count_points()
    spanish = games[session['key']].players[1].count_points()
    fields = empty_fields(games[session['key']].position, games[session['key']].ships)
    if pirates == 12 or spanish == 12:
        if pirates == 12:
            winner = "p"
        else:
            winner = "s"

        return render_template('solo/end.html', game=games[session['key']], fields=fields,
                               player=games[session['key']].active, pirates=pirates,
                               spanish=spanish, winner=winner)

    for player in games[session['key']].players:

        if player.state == 'active' and player.fleet == 's':
            return redirect(url_for('solo_move_computer'))

    return render_template('solo/board.html', game=games[session['key']], fields=fields,
                           player=games[session['key']].active, pirates=pirates, spanish=spanish)


@app.route('/solo/board/move/<name>')
def solo_move(name):
    if session.get('key') not in games:
        return redirect('/', code=302)
    if games[session['key']].ships[name].status == 'down':
        games[session['key']].ships[name].change_status()
        return redirect(url_for('solo_rotate', name=name))

    move = calculate_move(games[session['key']].ships[name].sails, games[session['key']].ships[name].direction,
                          games[session['key']].ships[name].x, games[session['key']].ships[name].y)
    moves = move_on_board(move, games[session['key']].position)

    free = free_fields(moves, games[session['key']].ships)
    turned = turned_down_fields(moves, games[session['key']].ships)
    enemy = enemy_fields(moves, games[session['key']].ships, games[session['key']].ships[name].fleet)

    fields = empty_fields(games[session['key']].position, games[session['key']].ships)
    return render_template('solo/move.html', game=games[session['key']], free=free, name=name, fields=fields,
                           enemy=enemy,
                           turned=turned)


@app.route('/solo/board/move/computer')
def solo_move_computer():

    if session.get('key') not in games:
        return redirect('/', code=302)
    computer_ships = list()
    computer_ships_up = list()
    human_ships_up = list()
    directions = ['left', 'right', 'up', 'down']
    rotations = {
        'left': 'right',
        'right': 'left',
        'up': 'down',
        'down': 'up'

    }
    fields = empty_fields(games[session['key']].position, games[session['key']].ships)

    for ship in games[session['key']].ships:

        if games[session['key']].ships[ship].status == 'down' or (
                games[session['key']].ships[ship].fleet == 's' and games[session['key']].ships[ship].status == 'up'):
            computer_ships.append(games[session['key']].ships[ship])
            if games[session['key']].ships[ship].status == 'up':
                computer_ships_up.append(games[session['key']].ships[ship].name)
        else:
            human_ships_up.append(games[session['key']].ships[ship].name)

    for ship1 in computer_ships:
        move = calculate_move(games[session['key']].ships[ship1.name].sails,
                              games[session['key']].ships[ship1.name].direction,
                              games[session['key']].ships[ship1.name].x,
                              games[session['key']].ships[ship1.name].y)
        moves = move_on_board(move, games[session['key']].position)
        enemy = enemy_fields(moves, games[session['key']].ships, games[session['key']].ships[ship1.name].fleet)
        if games[session['key']].ships[ship1.name].status == 'up' and games[session['key']].ships[
            ship1.name].state == 'visible':

            if len(enemy) != 0:
                for ship2 in games[session['key']].ships:
                    if (games[session['key']].ships[ship2].x, games[session['key']].ships[ship2].y) == \
                            enemy[0]:
                        return redirect(
                            url_for('solo_make_move_enemy', ship1=games[session['key']].ships[ship1.name].name,
                                    ship2=ship2))

    import random
    random.shuffle(computer_ships)

    for ship1 in computer_ships:
        move = calculate_move(games[session['key']].ships[ship1.name].sails,
                              games[session['key']].ships[ship1.name].direction,
                              games[session['key']].ships[ship1.name].x,
                              games[session['key']].ships[ship1.name].y)
        moves = move_on_board(move, games[session['key']].position)
        free = free_fields(moves, games[session['key']].ships)
        turned = turned_down_fields(moves, games[session['key']].ships)
        if len(free) != 0 and games[session['key']].ships[ship1.name].status == 'up' and games[session['key']].ships[
            ship1.name].state == 'visible':
            pole = fields.index(free[0])
            return redirect(
                url_for('solo_make_move_free', ship1=games[session['key']].ships[ship1.name].name, pole=pole))
        elif games[session['key']].ships[ship1.name].status == 'down' and (
                len(human_ships_up) > len(computer_ships_up) or len(computer_ships_up) == 0):
            games[session['key']].ships[ship1.name].change_status()
            import random
            random.shuffle(directions)
            return redirect(url_for('solo_rotate_change', name=games[session['key']].ships[ship1.name].name,
                                    direction=directions[0]))
        elif games[session['key']].ships[ship1.name].status == 'up' and len(turned) != 0 and \
                games[session['key']].ships[ship1.name].state == 'visible':
            for ship2 in games[session['key']].ships:
                if (games[session['key']].ships[ship2].x, games[session['key']].ships[ship2].y) == turned[0]:
                    return redirect(url_for('solo_make_move_turned', ship1=games[session['key']].ships[ship1.name].name,
                                            ship2=games[session['key']].ships[ship2].name))
        elif games[session['key']].ships[ship1.name].status == 'up' and games[session['key']].ships[
            ship1.name].state == 'visible':
            return redirect(url_for('solo_rotate_change', name=games[session['key']].ships[ship1.name].name,
                                    direction=rotations[games[session['key']].ships[ship1.name].direction]))
        elif games[session['key']].ships[ship1.name].status == 'down' and games[session['key']].ships[
            ship1.name].state == 'visible':
            games[session['key']].ships[ship1.name].change_status()
            import random
            random.shuffle(directions)
            return redirect(url_for('solo_rotate_change', name=games[session['key']].ships[ship1.name].name,
                                    direction=directions[0]))


@app.route('/solo/board/move/turned/<ship1>/<ship2>')
def solo_make_move_turned(ship1, ship2):
    if session.get('key') not in games:
        return redirect('/', code=302)
    a = (games[session['key']].ships[ship2].x, games[session['key']].ships[ship2].y)[:]
    if games[session['key']].ships[ship1].defeated:
        games[session['key']].ships[games[session['key']].ships[ship1].defeated].state = 'visible'

    games[session['key']].ships[ship1].change_location(a[0], a[1])
    games[session['key']].ships[ship1].defeated = games[session['key']].ships[ship2].name
    games[session['key']].ships[ship2].change_state(games[session['key']].ships[ship1].name)

    return solo_change_player()


@app.route('/solo/board/move/free/<ship1>/<pole>')
def solo_make_move_free(ship1, pole):
    if session.get('key') not in games:
        return redirect('/', code=302)
    fields = empty_fields(games[session['key']].position, games[session['key']].ships)
    if games[session['key']].ships[ship1].defeated:
        games[session['key']].games[session['key']][games[session['key']].ships[ship1].defeated].state = 'visible'
    games[session['key']].ships[ship1].change_location(fields[int(pole)][0], fields[int(pole)][1])
    return solo_change_player()


@app.route('/solo/board/move/enemy/<ship1>/<ship2>')
def solo_make_move_enemy(ship1, ship2):
    if session.get('key') not in games:
        return redirect('/', code=302)
    if games[session['key']].ships[ship1].defeated:
        games[session['key']].ships[games[session['key']].ships[ship1].defeated].state = 'visible'
        games[session['key']].ships[ship1].defeated = None
    a = (games[session['key']].ships[ship2].x, games[session['key']].ships[ship2].y)[:]
    games[session['key']].ships[ship1].change_location(a[0], a[1])
    games[session['key']].ships[ship2].change_location(0, 0)
    games[session['key']].ships[ship2].state = 'dead'
    if games[session['key']].ships[ship2].defeated:
        games[session['key']].ships[ship1].defeated = games[session['key']].ships[ship2].defeated

    for player in games[session['key']].players:
        if player.fleet == games[session['key']].ships[ship1].fleet:
            player.add_ship(games[session['key']].ships[ship2].name)

    return solo_change_player()


@app.route('/solo/board/rotate/<name>')
def solo_rotate(name):
    if session.get('key') not in games:
        return redirect('/', code=302)
    pirates = games[session['key']].players[0].count_points()
    spanish = games[session['key']].players[1].count_points()
    fields = empty_fields(games[session['key']].position, games[session['key']].ships)
    return render_template('solo/rotate.html', name=name, game=games[session['key']], fields=fields, pirates=pirates,
                           spanish=spanish)


@app.route('/solo/board/rotate/<name>/<direction>')
def solo_rotate_change(name, direction):
    if session.get('key') not in games:
        return redirect('/', code=302)
    games[session['key']].ships[name].change_direction(direction)
    return solo_change_player()


@app.route('/solo_change_player')
def solo_change_player():
    if session.get('key') not in games:
        return redirect('/', code=302)
    d = {
        'waiting': 'active',
        'active': 'waiting'
    }
    for player in games[session['key']].players:
        player.state = d[player.state]
        if player.count_points() == 12:
            redirect(url_for('solo_end', winner=player))

        else:
            if player.state == 'active':
                games[session['key']].change_active(str(player.fleet))

    return redirect(url_for('solo_board'))


@app.route('/solo/board/end/<winner>')
def solo_end(winner):
    if session.get('key')not in games:
        return redirect('/', code=302)
    return render_template('solo/rotate.html', game=games[session['key']], winner=winner)




if __name__ == '__main__':
    app.run(host="wierzba.wzks.uj.edu.pl", port=5129, debug=True)
