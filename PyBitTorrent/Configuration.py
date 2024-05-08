# Port to announce to tracker 
# port section at: 
#   https://wiki.theory.org/BitTorrent_Tracker_Protocol#Basic_Tracker_Announce_Request)
LISTENING_PORT = 6881

# Not implemented yet
MAX_LISTENING_PORT = 6889

# Maximun amount of peers to connect to
MAX_PEERS = 12

# Not implemented yet
REQUEST_INTERVAL = 0.2

# Interval between each piece request
ITERATION_SLEEP_INTERVAL = 0.001

# Logging level
#   https://docs.python.org/3/library/logging.html#logging.Logger.setLevel
LOGGING_LEVEL = 100

# Timeout for every request made
TIMEOUT = 3

# Number of handshakes to make in each thread with fixed amount of peers
# this value is inversely porportional to the number of threads created
MAX_HANDSHAKE_THREADS = 80


# Experimental options, DO NOT CHANGE

# Value to receive from UDP tracker requests
UDP_TRACKER_RECEIVE_SIZE = 16384

# Value to receive from peer requests, do not change
HANDSHAKE_STRIPPED_SIZE = 48

# Default connection ID for UDP tracker connections 
DEFAULT_CONNECTION_ID = 0X41727101980

# Bytes to read each iteration of compacted peers response, do not change
COMPACT_VALUE_NUM_BYTES = 6

# Use only TCP, ignore UDP
TCP_ONLY = False
