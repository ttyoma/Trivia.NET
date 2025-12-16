# Trivia.NET
A console-based trivia game built in Python using client-server architecture. The project features TCP socket communication, JSON-based message exchange, and multithreading to handle simultaneous players and asynchronous I/O, as well as an optional Ollama-powered AI integration to answer on the client's behalf.

# Features
- Client-server architecture using TCP socket communication
- Supports multiple concurrent players (with the same username as well)
- Customizable questions/responses as well as config information formattable via JSON
- Threaded handling of simultaneous connections
- Three different client modes (See Client Modes for more info)
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
Note: This pre-provided config file requires 2 players to run, and will wait indefinitely if only 1 client joins. (See Design Assumptions)

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
After all the players have connected, the server will begin the game.

All connected clients receive trivia questions and submit answers in real time.

Feedback and leaderboard updates are subsequently provided.

Note: Feel free to modify the existing configs/add your own JSON configs to play around with the program. (See Configuration Notes for more info)

## Context
This project was originally developed as part of a university networking assignment for INFO1112 Computing 1B OS and Network Platforms. As such, this implementation has some design choices that adhere to the assignment specifications. This repository has been cleaned and contains only the public implementation. Private course materials have been intentionally omitted in accordance with university policies. This project is solely for learning, experimentation, and portfolio demonstration. 

## Design Assumptions

- The server waits for a fixed number of players (as defined in the server config)
  before starting a game.
- If fewer players connect than required, the server will wait indefinitely.
- Players who disconnect mid-game remain on the leaderboard but can no longer score.
- Clients are expected to follow the defined JSON protocol.
- The server assumes well-formed configuration files.

## Client Modes
The client supports three different modes of playing:
- **manual (`you`)**  
  The client answers questions manually via standard input

- **automatic (`auto`)**  
  Questions are answered programmatically with perfect accuracy.  
  This mode exists to demonstrate deterministic problem-solving logic.

- **AI (`ai`)**  
  Questions are forwarded to a locally running Ollama instance, and the AI’s
  response is sent directly to the server without post-processing.

Note: The AI response is not guaranteed to always be correct

## Configuration Notes
- As mentioned before, server and client behavior is configurable via JSON files.
- All textual output (questions, feedback, leaderboards etc.) can be modified without altering the source code
- This allows for easier experimentation with pacing, difficulty, wording, localizations etc.
- 
When creating new config files, ensure that all of the required keys are present and correctly typed.
For a config to work, it must follow the following format:
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


## Troubleshooting

**Server appears to hang on startup**
- Ensure the number of connected clients matches the `players` value in the server config.

**Client connects, but nothing happens**
- The game only starts after all required players have joined. (Must not forget the CONNECT <HOSTNAME>:<PORT> command)
- Check that all clients are connecting to the same host and port.

**AI mode not responding**
- Ensure Ollama is running locally and accessible at the configured host/port.
- If Ollama is unavailable, use `manual` or `auto` mode instead.


## License
This project is licensed under the [Creative Commons Attribution–NonCommercial 4.0 International License (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/)
Feel free to use/modify this project for your own study learning or other non-commercial purposes, but provide credit when sharing online.


