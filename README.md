# Team-9-Class-A-Distributed-Multi-Channel-Chat-Application-with-MQTT-and-Threaded-Server

# Real-time Chat Application
Real-time chat application that allows users to communicate in channels and send private messages.
This is a simple **real-time chat application** built using **Python** and **sockets**. The application supports **channel-based communication** where users can send messages to a specific channel, as well as **private messages** for one-on-one communication.

## Features

- **Channel Communication**: Users can join and leave channels to participate in group conversations.
- **Private Messaging**: Users can send direct messages to other users using a specific command format.
- **Real-time Updates**: The app supports real-time message delivery with **socket programming**.
- **Multi-client Support**: Multiple users can connect to the server simultaneously and communicate independently.

## Components

- **Client**: Manages user input, sends and receives messages, and handles channel joining and private messaging.
- **Server**: Manages the connections of multiple clients, handles channel join/leave functionality, and ensures that messages are routed correctly.
  
## Requirements

- Python 3.x
- `socket` library (comes pre-installed with Python)
  
## Installation

Clone this repository to your local machine:

```bash
git clone <repository_url>
