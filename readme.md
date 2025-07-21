## <p align="center"><img src="hermes.png" alt="Hermes"></p>

# Hermes: Your Topic-Based WebSocket Message Broker

Hermes is a lightweight and efficient Python WebSocket server designed for real-time broadcasting of messages based on topics. Inspired by the swift messenger god Hermes, this server facilitates the distribution of data to clients that have subscribed to specific channels or topics of interest.

## What Does Hermes Do?

Hermes acts as a central hub for publish/subscribe (pub/sub) messaging over WebSockets. Here's a breakdown of its key functionalities:

* **Topic-Based Subscriptions:** Clients can subscribe to specific topics (e.g., `stock:AAPL`, `news:technology`, `sensor:temperature`). They will only receive messages published to the topics they are interested in.
* **Real-time Broadcasting:** When a message is sent to a particular topic, Hermes efficiently broadcasts that message to all currently connected clients that are subscribed to that topic.
* **Lightweight and Efficient:** Built using the [`websockets`](https://websockets.readthedocs.io/) library in Python, Hermes is designed to be performant and handle a significant number of concurrent WebSocket connections with minimal resource usage.
* **Simple Protocol:** Clients interact with Hermes using simple JSON messages for subscribing, unsubscribing, and (optionally, for producers) publishing data.

## Key Features

* **Easy Integration:** Simple WebSocket protocol makes it easy to integrate with various front-end and back-end technologies.
* **Scalable:** Designed to handle a growing number of clients and topics.
* **Robust Connection Handling:** Gracefully handles client connections and disconnections, cleaning up subscriptions automatically.
* **Clear Topic Management:** Provides visibility into active topics and the number of subscribers for each.
* **Error Handling:** Includes basic error reporting to clients for malformed requests.

## Getting Started

### Prerequisites

* Python 3.7 or higher

### Running Hermes

1.  **Clone the repository (if you have the code):**

    ```bash
    git clone [your_repository_link]
    cd hermes
    ```

2.  **Install dependencies:**

    ```bash
    pip install websockets
    ```

3.  **Run the Hermes server:**

    ```bash
    python your_server_script_name.py  # Replace with the actual name of your Python server file
    ```


### Client Interaction

Clients interact with Hermes by sending and receiving JSON messages over a WebSocket connection.

#### Subscribing to a Topic

To subscribe to a topic, send a JSON message with the `type` set to `"subscribe"` and the desired `topic`:

\`\`\`json
{"type": "subscribe", "topic": "stock:GOOGL"}
\`\`\`

Hermes will respond with an acknowledgment:

\`\`\`json
{"type": "ack_subscribe", "topic": "stock:GOOGL", "message": "Successfully subscribed to stock:GOOGL"}
\`\`\`

#### Unsubscribing from a Topic

To unsubscribe from a topic, send a JSON message with the `type` set to `"unsubscribe"` and the `topic` to unsubscribe from:

\`\`\`json
{"type": "unsubscribe", "topic": "news:sports"}
\`\`\`

Hermes will respond with an acknowledgment:

\`\`\`json
{"type": "ack_unsubscribe", "topic": "news:sports", "message": "Successfully unsubscribed from news:sports"}
\`\`\`

#### Publishing Data to a Topic (Optional - for data producers)

To send data to a specific topic (if your application logic allows certain clients to publish), send a JSON message with the `topic` and a `data` payload:

\`\`\`json
{"topic": "stock:AAPL", "data": {"price": 170.50, "timestamp": "2024-10-27T10:00:00Z"}}
\`\`\`

Hermes will then broadcast this `data` to all clients subscribed to the `stock:AAPL` topic.

## Use Cases

Hermes is ideal for applications that require real-time data updates and event broadcasting, such as:

* Live financial data feeds (stock tickers, cryptocurrency prices)
* Real-time dashboards and monitoring systems
* Chat applications and collaborative tools
* Gaming and interactive experiences
* IoT sensor data streaming
* Notifications and alerts

## Configuration

The Hermes server can be configured using environment variables:

* `WS_PORT`: The port on which the WebSocket server will listen (default: `443`).




