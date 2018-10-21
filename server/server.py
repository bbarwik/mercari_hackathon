import http.server
import socketserver
import io
from subprocess import call
from ewmh import EWMH
import threading
import time

ewmh = EWMH()

games = {
    252950: b'Rocket League',
    730: b'Counter-Strike: Global Offensive - OpenGL'
}

working_thread = None


def get_window_by_name(name):
    wins = ewmh.getClientList()
    for win in wins:
        try:
            if ewmh.getWmName(win) == name:
                return win
        except:
            pass
    return None


def secutity_monitoring(window_name):
    bad = 0
    while working_thread:
        window = get_window_by_name(window_name)
        if not window:
            bad += 1
            if bad > 20:
                # application is closed, end of session
                print("Killing vnc, game not working")
                call(['killall', 'x11vnc'])
                break
        else:
            bad = 0
        active = ewmh.getActiveWindow()
        if window and active != window:
            ewmh.setActiveWindow(window)
            ewmh.display.flush()
            time.sleep(0.1)
            active = ewmh.getActiveWindow()
            if active != window:
                bad += 1
                if bad > 20:
                    # application is closed or bugged, end of session
                    print("Killing vnc, game probably bugged")
                    call(['killall', 'x11vnc'])            
                    break
            else:
                bad = 0
        time.sleep(0.1)
    window = get_window_by_name(window_name)
    if window: # end of session, killing game
        pid = ewmh.getWmPid(window)
        call(['kill', '-9', str(pid)])


def start_vnc_session(process_name):
    global working_thread
    window = get_window_by_name(process_name)
    if not window:
        print("Cant find correct window, sleep for 5 s and trying one more time")
        time.sleep(5)
        window = get_window_by_name(process_name)
        if not window:
            print("Cant find correct window, aborting")
            return
    
    ewmh.setActiveWindow(window)
    ewmh.display.flush()

    thread = threading.Thread(target=secutity_monitoring, args=(process_name, ))
    working_thread = True
    thread.start()
    print("Starting vnc for {}".format(process_name))
    call(['x11vnc', '-wait', '1', '-defer', '1', '-geometry', '1280x800'])
    working_thread = None


def start_steam_game(app_id):
    call(['steam', 'steam://rungameid/{}'.format(int(app_id))])


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
            game_id = int(self.path[1:])
        except ValueError:
            game_id = 0

        ret = b"ERROR"
        if game_id in games and not working_thread:
            ret = b"OK"
            game_name = games[game_id]
            if get_window_by_name(game_name) is None:
                start_steam_game(game_id)
                for i in range(10):
                    if get_window_by_name(game_name):
                        break
                    time.sleep(1)
                else:
                    return

            time.sleep(3)                     
            thread = threading.Thread(target=start_vnc_session, args=(game_name, ))       
            thread.start()          

        self.send_response(200 if ret == b"OK" else 404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(ret)

print('GameShare server on port 8000...')
httpd = socketserver.TCPServer(('0.0.0.0', 8000), Handler)
call(['killall', 'x11vnc']) # just in case
try:
    httpd.serve_forever()
except:
    pass
print("Closing server")
httpd.server_close()