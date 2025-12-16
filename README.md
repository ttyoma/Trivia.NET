# Trivia.NET
A console-based trivia game built in Python using client-server architecture. The project featuring TCP socket communication, JSON-based message exchange, and multithreading to handle simultaneous players and asynchronous I/O, as well as an optional Ollama-powered AI integration to answer on the clients behalf.

# Features
- Client-server architecture using TCP socket communication
- Supports multiple concurrent players (with the same username as well)
- Customizable questions/responses as well as config information formattable via JSON
- Threaded handling of simultaneous connections
- Three different client modes (manual: Client plays for themselves, auto: Automatic answering on the client's behalf with perfect accuracy, ai: Ollama AI answers on the clients behalf)
- Graceful disconnects for different scenarios (such as mid-round disconnects)

# How to Run

### You will need
- Python 3.10 or newer
- Ollama installed and running (optional)

### Instructions

#### 1. Clone the repository
```bash
git clone https://github.com/ttyoma/trivia-net.git
cd trivia-net
```

#### 2. Start the server
```bash
python3 server.py --config <config_path>
```

If you wish to use the pre-provided config files, use 
```bash
python3 server.py --config configs/server_config.json
```
Note: This pre-provided config file requires 2 players to run, and will wait indefinitely if only 1 client joins. 

#### 3. Start the client/s in separate terminals
```bash
python3 client.py --config <config_path>
CONNECT <HOSTNAME>:<PORT>
```

If you wish to use the pre-provided config files, use 
```bash
python3 client.py --config configs/client_config.json
CONNECT 127.0.0.1:7777
```

In another terminal:
```bash
python3 client.py --config configs/client2_config.json
CONNECT 127.0.0.1:7777
```

#### 4. Play the trivia game
 Answer the questions within the time limit and have fun

 Note: Feel free to modify the existing configs/add your own JSON configs to play around with the program. For a config to work, it must follow the following format:
```
 {
 "port": <int>,
 "players": <int>,
 "question_formats": <dict>,
 "question_types": [<str>],
 "question_seconds": <int> | <float>,
 "question_interval_seconds": <int> | <float>,
 "ready_info": <str>,
 "question_word": <str>,
 "correct_answer": <str>,
 "incorrect_answer": <str>,
 "points_noun_singular": <str>,
 "points_noun_plural": <str>,
 "final_standings_heading": <str>,
 "one_winner": <str>,
 "multiple_winners": <str>
}
```

# License
This project is licensed under the [Creative Commons Attribution–NonCommercial 4.0 International License (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/)
Feel free to use/modify this project for your own study learning or other non-commercial purposes, but provide credit when sharing online.


