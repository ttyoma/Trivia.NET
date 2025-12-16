#AI Acknowledgement - Artificial Intelligence was used for debugging sometimes, as well as giving me a second opinion on analyzing the possible reasons behind some testcases failing

import json
import requests
import sys
import socket
import select
import threading
from pathlib import Path
from threading import Event
from typing import Any, Literal
from queue import Queue, Empty

current_conn: socket.socket | None = None
listener_thread: threading.Thread | None = None

game_active = False
awaiting_answer = False
answer_queue: "Queue[str]" = Queue()
shutdown_flag = Event()
last_answer = ""

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

def receive_message(connection: socket.socket, timeout: float = 2.0) -> dict[str, Any]:
    buffer = b""
    connection.setblocking(False)
    while True:
        if shutdown_flag.is_set() or connection.fileno() == -1:
            return
        
        try:
            ready, _, _ = select.select([connection], [], [], timeout)
        except (ValueError, OSError):
            return
        
        if not ready:
            continue

        try:
            chunk = connection.recv(1024)
        except (ConnectionResetError, OSError):
            return

        if not chunk:
            if buffer.strip():
                try:
                    yield decode_message(buffer)
                except Exception:
                    pass
            return
        
        buffer += chunk

        while b"\n" in buffer:
            raw, _, buffer = buffer.partition(b"\n")
            try:
                yield decode_message(raw)
            except json.JSONDecodeError:
                continue

# === HANDLE CONNECTIONS ===

def connect(host: str, port: int, username: str) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except Exception:
        print("Connection failed")
        sys.exit(1)
    
    hi_message = {"message_type": "HI", "username": username}
    send_message(sock, hi_message)
    return sock

def disconnect(connection: socket.socket):
    bye_message = {"message_type": "BYE"}
    try:
        send_message(connection, bye_message)
    except OSError:
        pass
    try:
        if connection.fileno() != -1:
            connection.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    try:
        connection.close()
        shutdown_flag.set()
    except OSError:
        pass

# === QUESTION LOGIC AND HELPERS ===

def answer_question(question_type: str, short_question: str, question_text: str, time_limit: float, 
                    client_mode: Literal["you", "auto", "ai"], ollama_config: dict[str, Any] | None) -> str:
    
    if client_mode == "you":
        global awaiting_answer
        awaiting_answer = True
        try:
            try:
                ans = answer_queue.get(timeout=time_limit)
            except Empty:
                return None
            if ans is None:
                return None  
            return ans
        finally:
            awaiting_answer = False

    elif client_mode == "auto":
        question_type = question_type.strip().lower()
        if "mathematics" in question_type:
            return answer_math(short_question)
        elif "roman" in question_type:
            return str(answer_roman(short_question))
        elif "usable" in question_type:
            return answer_usable_addresses(short_question)
        elif "broadcast" in question_type or "network" in question_type:
            return answer_network_broadcast(short_question)
        else:
            return ""
    
    elif client_mode == "ai":
        try:
            answer = answer_question_ollama(question_text, time_limit, ollama_config or {})
        except Exception:
            answer = ""
        return answer
    
    else:
        print("Unknown client mode")
        return ""

def answer_question_ollama(question_text: str, time_limit: float, ollama_config: dict[str, Any]) -> str:
    
    host = ollama_config["ollama_host"]
    port = ollama_config["ollama_port"]
    model = ollama_config["ollama_model"]

    #ngl this part of this assignment is just so cool, insane props to teaching team y'alls

    ai_prompt = (
        "ONLY answer the question with the FINAL ANSWER without any greetings, explanation or any kind of fluff. For math questions," 
        "answer with ONLY the final value. For roman numerals, answer with ONLY the decimal. For a usable IP question, answer with "
        "ONLY the number of usable IPs. For a network/broadcast question answer with ONLY 'network and broadcast' (eg. 192.168.1.0 and 192.168.1.255)"
    )

    user_prompt = question_text

    url = f"http://{host}:{port}/api/chat"

    ai_message = {
        "model": model,
        "messages": [
            {"role": "system", "content": ai_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }

    result = {"answer": ""}

    def do_request():
        try:
            r = requests.post(url, json=ai_message, timeout=time_limit)
            r.raise_for_status()
            data = r.json()
            result["answer"] = (data.get("message", {}).get("content") or "")
        except Exception:
            result["answer"] = None

    worker = threading.Thread(target=do_request, daemon=True)
    worker.start()
    worker.join(timeout=time_limit)

    if worker.is_alive():
        return None
    return result["answer"]

def get_ollama_configs(config: dict[str, Any]) -> dict[str, Any] | None:

    mode = config.get("client_mode", "").strip().lower()
    if mode != "ai":
        return None
    
    ollama_config = config.get("ollama_config")
    if not ollama_config or not all(k in ollama_config for k in ("ollama_host", "ollama_port", "ollama_model")): 
        print("client.py: Missing values for Ollama configuration", file=sys.stderr)
        sys.exit(1)

    return ollama_config

def automatic_answer(question_type: str, short_question: str) -> str:

    question_type = question_type.strip().lower()
    if "mathematics" in question_type:
        return answer_math(short_question)
    elif "roman" in question_type:
        return str(answer_roman(short_question))
    elif "usable" in question_type:
        return answer_usable_addresses(short_question)
    elif "broadcast" in question_type or "network" in question_type:
        return answer_network_broadcast(short_question)
    else:
        return ""

def answer_math(expr: str) -> str:

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

def answer_roman(s: str) -> str:

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

def answer_usable_addresses(subnet: str) -> str:

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

def answer_network_broadcast(subnet: str) -> str:

    ip_str, prefix = subnet.split('/')
    prefix = int(prefix)
    ip_int = ip_to_int(ip_str)
    mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
    network = ip_int & mask
    broadcast = network | (~mask & 0xFFFFFFFF)
    return f"{int_to_ip(network)} and {int_to_ip(broadcast)}"

# === HANDLE MESSAGES ===

def handle_question(message: dict[str, Any], connection: socket.socket, client_mode: Literal["you", "auto", "ai"], ollama_config: dict[str, Any] | None):

    global last_answer
    question_text = message.get("question") or message.get("trivia_question", "")
    question_type = message.get("question_type", "")
    short_question = message.get("short_question", "")
    time_limit = float(message.get("time_limit", 0))

    print(question_text)

    answer = answer_question(question_type, short_question, question_text, time_limit, client_mode, ollama_config)
    last_answer = answer

    if answer is not None:
        send_message(connection, {
                    "message_type": "ANSWER",
                    "answer": answer
                })

def handle_received_message(message: dict[str, Any], connection: socket.socket, client_mode: Literal["you", "auto", "ai"], ollama_config):

    global game_active
    message_type = message.get("message_type", "").strip().upper()

    if message_type == "READY":
        game_active = True
        print(message["info"])

    elif message_type == "QUESTION":
        handle_question(message, connection, client_mode, ollama_config)

    elif message_type == "RESULT":
        if last_answer.strip() != "":
            print(message["feedback"])

    elif message_type == "LEADERBOARD":
        print(message['state'])

    elif message_type == "FINISHED":
        print(message["final_standings"])
        game_active = False

        try:
            send_message(connection, {"message_type": "BYE"})
        except Exception:
            pass
 
        disconnect(connection)
        shutdown_flag.set()

    else:
        print("Received:", message)

def listener(sock, client_mode, ollama_config):
    run_client_session(sock, client_mode, ollama_config)

# === HANDLE MAIN SESSION LOOP ===

def handle_command(command: str, username: str, client_mode: str, ollama_config,
                   current_conn: socket.socket | None, listener_thread: threading.Thread | None):
    
    parts = command.strip().split()
    if not parts:
        return current_conn, listener_thread

    command = parts[0].upper()

    if command == "CONNECT" and len(parts) > 1:
        if current_conn is not None:
            print("Already connected.")
            return current_conn, listener_thread
        try:
            shutdown_flag.clear()
            host, port_str = parts[1].split(":")
            sock = connect(host, int(port_str), username)
            lt = threading.Thread(target=listener, args=(sock, client_mode, ollama_config), daemon=True)
            lt.start()
            return sock, lt
        except ValueError:
            print("Connection failed.")

    elif command == "DISCONNECT":
        if current_conn:
            shutdown_flag.set()
            disconnect(current_conn)  #If connected, sends bye
            if listener_thread:
                listener_thread.join(timeout=0.5)
            #print("Disconnected.")
            return None, None
        else:
            return None, None

    elif command == "EXIT":
        if current_conn:
            shutdown_flag.set()
            disconnect(current_conn) #If connected, send bye, exit program
            if listener_thread:
                listener_thread.join(timeout=0.5)
        sys.exit(0)

    else:
        #Invalid COmmand
        return current_conn, listener_thread

def run_client_session(sock: socket.socket, client_mode: str, ollama_config):

    finished = False
    try:
        for message in receive_message(sock):  
            if shutdown_flag.is_set() or sock.fileno() == -1:
                break
            handle_received_message(message, sock, client_mode, ollama_config)
            msg_type = message.get("message_type", "").strip().upper()
            if msg_type == "FINISHED":
                finished = True
                break
    except (ValueError, OSError):
        pass

def main():

    if len(sys.argv) < 3 or sys.argv[1] != "--config":
        print("client.py: Configuration not provided", file=sys.stderr)
        sys.exit(1)

    config_path = Path(sys.argv[2])
    if not config_path.exists():
        print(f"client.py: File {config_path} does not exist", file=sys.stderr)
        sys.exit(1)
    
    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)
    
    username = config["username"]
    client_mode = config["client_mode"]
    if client_mode == "ai":
        ollama_config = get_ollama_configs(config)
    else:
        ollama_config = None

    current_conn = None
    listener_thread = None
    global game_active

    while True:
        try:
            line = input("")
        except EOFError:
            if current_conn:
                disconnect(current_conn)
            break

        upper = line.upper()

        #Priority to commands
        if upper in ("EXIT", "DISCONNECT") or upper.startswith("CONNECT"):
            current_conn, listener_thread = handle_command(
                line, username, client_mode, ollama_config,
                current_conn, listener_thread
            )
            continue

        if awaiting_answer and client_mode == "you":

            answer_queue.put(line)
            continue
        
if __name__ == "__main__":
    main()