#AI Acknowledgement - Artificial Intelligence was used for debugging sometimes, as well as giving me a second opinion on analyzing the possible reasons behind some testcases failing

import json
import socket
import sys
import time
import select
import threading
from pathlib import Path
from typing import Any

from questions import (
    generate_mathematics_question,
    generate_roman_numerals_question,
    generate_usable_addresses_question,
    generate_network_broadcast_question
)

# === HANDLE MESSAGES ===

def encode_message(message: dict[str, Any]) -> bytes:
    return (json.dumps(message) + "\n").encode("utf-8")

def decode_message(data: bytes) -> dict[str, Any]:
    return json.loads(data.decode("utf-8"))

def send_message(connection: socket.socket, data: dict[str, Any]):
    try:
        connection.sendall(encode_message(data))
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass

def receive_message(connection: socket.socket) -> dict[str, Any]:
    buffer = b""
    while True:
        try:
            chunk = connection.recv(1024)
        except OSError:
            return None

        if not chunk:
            if buffer.strip():
                try:
                    return decode_message(buffer)
                except Exception:
                    return None
            return None

        buffer += chunk

        if b"\n" in buffer:
            raw, _, buffer = buffer.partition(b"\n")
            try:
                return decode_message(raw)
            except Exception:

                buffer = b""
                continue
        try:
            return decode_message(buffer)
        except json.JSONDecodeError:

            continue

# === HANDLE QUESTIONS ===

def normalize_question_type(qtype: str) -> str:

    q = qtype.strip().lower().replace("_", " ")
    mapping = {
        "mathematics": "Mathematics",
        "roman numerals": "Roman Numerals",
        "usable ip addresses of a subnet": "Usable IP Addresses of a Subnet",
        "usable addresses": "Usable IP Addresses of a Subnet",
        "network and broadcast address of a subnet": "Network and Broadcast Address of a Subnet",
        "network broadcast": "Network and Broadcast Address of a Subnet",
    }
    return mapping.get(q)

def generate_question(question_type: str, config: dict[str, Any], 
                      question_num: int) -> dict[str, Any]:
    
    key = normalize_question_type(question_type)
    if key is None:
        print(f"server.py: Unknown question type '{question_type}'", file=sys.stderr)
        sys.exit(1)

    if key == "Mathematics":
        short_question = generate_mathematics_question()
    elif key == "Roman Numerals":
        short_question = generate_roman_numerals_question()
    elif key == "Usable IP Addresses of a Subnet":
        short_question = generate_usable_addresses_question()
    elif key == "Network and Broadcast Address of a Subnet":
        short_question = generate_network_broadcast_question()

    question_format = config["question_formats"][key]
    formatted_question = question_format.format(short_question)
    trivia_question = f"{config['question_word']} {question_num} ({key}):\n{formatted_question}"

    return {
        "message_type": "QUESTION",
        "question_type": key,
        "short_question": short_question,
        "trivia_question": trivia_question,
        "time_limit": config["question_seconds"]
    }

def generate_question_answer(question_type: str, short_question: str) -> str:

    key = normalize_question_type(question_type)
    if key is None:
        print(f"server.py: Unknown question type '{question_type}'", file=sys.stderr)
        sys.exit(1)

    if key == "Mathematics":
        return answer_mathematics_question(short_question)
    elif key == "Roman Numerals":
        return roman_to_int(short_question)
    elif key == "Usable IP Addresses of a Subnet":
        return answer_usable_addresses_question(short_question)
    elif key == "Network and Broadcast Address of a Subnet":
        return answer_network_broadcast_question(short_question)
    
# === HANDLE ANSWER COMPUTATION ===

def answer_mathematics_question(expr: str) -> str:
    tokens = expr.split()   
    total = int(tokens[0])
    i = 1

    while i < len(tokens):
        operator = tokens[i]
        operand = int(tokens[i + 1])
        if operator == '+':
            total += operand
        elif operator == '-':
            total -= operand
        i += 2

    return str(total)

def roman_to_int(s: str) -> str:
    vals = {
        'I': 1, 'V': 5, 'X': 10, 'L': 50,
        'C': 100, 'D': 500, 'M': 1000
    }

    total = 0
    prev_value = 0
    for char in reversed(s):
        value = vals[char]
        if value < prev_value:
            total -= value
        else:
            total += value
        prev_value = value
    return str(total)

def answer_usable_addresses_question(subnet: str) -> str:
    _, prefix = subnet.split('/')
    prefix = int(prefix)
    total_addresses = 2 ** (32 - prefix)
    usable_addresses = max(total_addresses -2, 0)
    return str(usable_addresses)

def ip_to_int(ip_str: str) -> int:
    parts = [int(part) for part in ip_str.split('.')]
    n = (parts[0] << 24) + (parts[1] << 16) + (parts[2] << 8) + parts[3]
    return n

def int_to_ip(n: int) -> str:
    return f"{(n >> 24) & 255}.{(n >> 16) & 255}.{(n >> 8) & 255}.{n & 255}"

def answer_network_broadcast_question(subnet: str) -> str:
    ip_str, prefix = subnet.split('/')
    prefix = int(prefix)
    ip_int = ip_to_int(ip_str)
    mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
    network = ip_int & mask
    broadcast = network | (~mask & 0xFFFFFFFF)
    return f"{int_to_ip(network)} and {int_to_ip(broadcast)}"

# === HANDLE TRIVIA FEATURES ===

def start_round(connections, usernames, config: dict[str, Any]):

    scores = {addr: 0 for addr in connections.keys()}
    total_questions = len(config["question_types"])
    disconnected: set[tuple[str, int]] = set()

    for question_num, question_type in enumerate(config["question_types"], start=1):
        question_data = generate_question(question_type, config, question_num)

        # --- Thread threads(?)
        results = {}
        threads = []

        def run_for_player(addr, conn, username):
            points = handle_game_round(conn, username, question_data, config)
            results[addr] = points

        for addr, conn in connections.items():
            if addr in disconnected:
                continue
            username = usernames[addr]
            t = threading.Thread(target=run_for_player, args=(addr, conn, username), daemon=True)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()  # wait for all players questions to complete

        # --- Merge threads
        for addr, points in results.items():
            if points is None:
                disconnected.add(addr)
                continue
            scores[addr] += points

        # Create and send leaderboard to all active players
        if question_num < total_questions:
            leaderboard_text = generate_leaderboard_state(scores, usernames, config)
            leaderboard_message = {
                "message_type": "LEADERBOARD",
                "state": leaderboard_text
            }

            for addr, conn in connections.items():
                if addr in disconnected:
                    continue
                send_message(conn, leaderboard_message)
                print("Leaderboard sent.")
            time.sleep(config["question_interval_seconds"])

    end_round(connections, usernames, scores, config)

def handle_game_round(conn: socket.socket, username: str, question_data: dict[str, Any], 
                      config: dict[str, Any]) -> int:
#Main game logic - Send questions, receive answers, returns score
#Returns None for DCs

    question_message = {
        "message_type": "QUESTION",
        "question_type": question_data["question_type"],
        "short_question": question_data["short_question"],
        "time_limit": config["question_seconds"],
        "trivia_question": question_data["trivia_question"],
    }

    send_message(conn, question_message)
    print(f"Sent question to {username}: {question_data['trivia_question']}")

    timeout = question_data["time_limit"]

    try:
        if conn.fileno() == -1:
            return None
        readable, _, _ = select.select([conn], [], [], timeout)
    except (ValueError, OSError):
        return None

    if not readable:
        #Player timed out
        return 0
    else:
        answer_message = receive_message(conn)
        if answer_message is None:
            print(f"{username} disconnected")
            try:
                conn.close()
            except OSError:
                pass
            return None
        
        message_type = (answer_message.get("message_type") or "")
        if message_type == "BYE":
            print(f"{username} disconnected")
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                conn.close()
            except OSError:
                pass
            return None
        
        player_answer = str(answer_message.get("answer", ""))#.split() LMAO good testcase

    correct_answer = str(generate_question_answer(
        question_data["question_type"], 
        question_data["short_question"]
    ))
    
    extra_vals = {
    "answer": player_answer,
    "correct_answer": correct_answer,
    "question": question_data["trivia_question"],
    }

    if player_answer == correct_answer:
        feedback = anti_key_error(config["correct_answer"], config, extra_vals)
        points = 1
    else:
        feedback = anti_key_error(config["incorrect_answer"], config, extra_vals)
        points = 0
    
    if player_answer is None:
        return 0
    
    if player_answer is not None:

        result_message = {
            "message_type": "RESULT",
            "correct": player_answer == correct_answer,
            "feedback": feedback
        }
        
        send_message(conn, result_message)
        print(f"Player answer: {player_answer}, Correct answer: {correct_answer}")

    return points

def generate_leaderboard_state(scores: dict[tuple[str,int], int], usernames, config: dict[str, Any]) -> str:

    rows = [(addr, usernames.get(addr, "?"), score) for addr, score in scores.items()]
    rows.sort(key=lambda r: (-r[2], r[1], r[0]))

    lines = []
    rank = 1
    prev_score = None
    players_seen = 0

    for _, uname, points in rows:
        players_seen += 1
        if prev_score is not None and points < prev_score:
            rank = players_seen
        prev_score = points

        if points == 1:
            noun = config["points_noun_singular"]
        else:
            noun = config["points_noun_plural"]

        lines.append(f"{rank}. {uname}: {points} {noun}")

    return "\n".join(lines)

def end_round(connections, usernames, scores, config: dict[str, Any]):

    rows = [(addr, usernames.get(addr, "?"), score) for addr, score in scores.items()]
    rows.sort(key=lambda r: (-r[2], r[1], r[0]))

    top = rows[0][2]
    winner_addrs = [addr for addr, _, points in rows if points == top]
    winners = [usernames.get(addr, "?") for addr in winner_addrs]

    lines = [anti_key_error(config["final_standings_heading"], config)]
    rank = 1
    prev_score = None
    players_seen = 0

    for _, uname, points in rows:
        players_seen += 1
        if prev_score is not None and points < prev_score:
            rank = players_seen
        prev_score = points

        if points == 1:
            noun = config["points_noun_singular"]
        else:
            noun = config["points_noun_plural"]
        
        lines.append(f"{rank}. {uname}: {points} {noun}")

    winners_str = ", ".join(winners)

    one_winner = anti_key_error(config["one_winner"], config, {"winners": winners_str}, *winners)
    multiple_winners = anti_key_error(config["multiple_winners"], config, {"winners": winners_str}, winners_str)

    if len(winners) == 1:
        lines.append(one_winner)
    else:
        lines.append(multiple_winners)

    final_standings = "\n".join(lines)

    finished_message = {
        "message_type": "FINISHED",
        "final_standings": final_standings
    }

    for addr, conn in connections.items():
        try:
            send_message(conn, finished_message)
        except Exception:
            pass

    for addr, conn in connections.items():
        try:
            conn.close()
        except Exception:
            pass

# --- OTHER HELPERS

def read_hi_message(conn: socket.socket, timeout: float = 2.0) -> dict[str, Any] | None:

    conn.setblocking(False)
    buffer = b""
    start = time.time()

    while time.time() - start < timeout:
        try:
            chunk = conn.recv(1024)
        except BlockingIOError:
            time.sleep(0.05)
            continue
        except OSError:
            return None

        if not chunk:
            time.sleep(0.05)
            continue

        buffer += chunk
        try:
            msg = decode_message(buffer)
            return msg
        except json.JSONDecodeError:
            continue

    return None  # timeout

def anti_key_error(template, config, extra=None, *positional):

    vals = dict(config)
    n = len(config.get("question_types", []))
    vals.update({
        "total_questions": n,
        "num_questions": n,
        "questions": n,
        "Questions": n,
        "len(question_types)": n,
    })
    if extra:
        vals.update(extra)
    try:
        return template.format(*positional, **vals)
    except Exception:
        return template

# --- MAIN

def main():
    # --- Check basic setup ---
    if len(sys.argv) < 3 or sys.argv[1] != "--config":
        print("server.py: Configuration not provided", file=sys.stderr)
        sys.exit(1)
    config_path = Path(sys.argv[2])
    if not config_path.exists():
        print(f"server.py: File {config_path} does not exist", file=sys.stderr)
        sys.exit(1)
    
    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)
    
    port = config["port"]
    max_players = config["players"]

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_sock.bind(("0.0.0.0", port))
    except OSError:
        print(f"server.py: Binding to port {port} was unsuccessful", file=sys.stderr)
        sys.exit(1)
    
    server_sock.listen(max_players)
    print(f"Server listening on port {port}...")

    # --- Player checks

    connections: dict[tuple[str, int], socket.socket] = {}
    usernames: dict[tuple[str, int], str] = {}

    while len(connections) < max_players:
        conn, addr = server_sock.accept()
        print(f"Accepted connection from {addr}")
        connections[addr] = conn

    for addr, conn in list(connections.items()):
        message = read_hi_message(conn)
        if message is None:
            conn.close()
            del connections[addr]
            continue

        username = message.get("username", "")
        if not isinstance(username, str):
            print(f"Invalid username from {addr}")
            conn.close()
            del connections[addr]
            continue

        usernames[addr] = username
        print(f"Player joined: {username} from {addr}")
    
    if usernames:
        ready_info = anti_key_error(config["ready_info"], config)
        ready_message = {"message_type": "READY", "info": ready_info}

        for addr, conn in connections.items():
            send_message(conn, ready_message)

        time.sleep(config["question_interval_seconds"])

        start_round(connections, usernames, config)
        sys.exit(0)

if __name__ == "__main__":
    main()