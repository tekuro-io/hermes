import asyncio
import websockets
import json
import os
from collections import defaultdict

#       ___           ___           ___           ___           ___           ___              
#      /\  \         /\__\         /\  \         /\  \         /\__\         /\__\             
#      \:\  \       /:/ _/_       /::\  \       |::\  \       /:/ _/_       /:/ _/_            
#       \:\  \     /:/ /\__\     /:/\:\__\      |:|:\  \     /:/ /\__\     /:/ /\  \           
#   ___ /::\  \   /:/ /:/ _/_   /:/ /:/  /    __|:|\:\  \   /:/ /:/ _/_   /:/ /::\  \          
#  /\  /:/\:\__\ /:/_/:/ /\__\ /:/_/:/__/___ /::::|_\:\__\ /:/_/:/ /\__\ /:/_/:/\:\__\         
#  \:\/:/  \/__/ \:\/:/ /:/  / \:\/:::::/  / \:\~~\  \/__/ \:\/:/ /:/  / \:\/:/ /:/  /         
#   \::/__/       \::/_/:/  /   \::/~~/~~~~   \:\  \        \::/_/:/  /   \::/ /:/  /          
#    \:\  \        \:\/:/  /     \:\~~\        \:\  \        \:\/:/  /     \/_/:/  /           
#     \:\__\        \::/  /       \:\__\        \:\__\        \::/  /        /:/  /            
#      \/__/         \/__/         \/__/         \/__/         \/__/         \/__/    
#
# A Python WebSocket server for topic-based broadcasting

# --- Configuration ---
WS_PORT = int(os.environ.get('WS_PORT', 8080))

TOPIC_SUBSCRIPTIONS = defaultdict(set)
CLIENT_TOPICS = defaultdict(set)

async def register_client(websocket):
    """Registers a new WebSocket client and sends a welcome message."""
    print(f"Client connected: {websocket.remote_address}")
    await websocket.send(json.dumps({"type": "info", "message": "Connected to HERMES WebSocket server. Send {'type': 'subscribe', 'topic': 'stock:TICKER'} to subscribe."}))

async def unregister_client(websocket):
    """Unregisters a disconnected WebSocket client and cleans up its topic subscriptions."""
    print(f"Client disconnected: {websocket.remote_address}. Cleaning up subscriptions.")
    topics_to_remove = CLIENT_TOPICS.pop(websocket, set()) # Get and remove client's topics

    for topic in topics_to_remove:
        if websocket in TOPIC_SUBSCRIPTIONS[topic]:
            TOPIC_SUBSCRIPTIONS[topic].remove(websocket)
            if not TOPIC_SUBSCRIPTIONS[topic]:
                del TOPIC_SUBSCRIPTIONS[topic]
                print(f"Topic '{topic}' has no more subscribers and was removed.")
    
    print(f"Current active topics: {list(TOPIC_SUBSCRIPTIONS.keys())}")

async def subscribe_client_to_topic(websocket, topic: str):
    TOPIC_SUBSCRIPTIONS[topic].add(websocket)
    CLIENT_TOPICS[websocket].add(topic)
    print(f"Client {websocket.remote_address} SUBSCRIBED to topic: '{topic}'. Subscribers for '{topic}': {len(TOPIC_SUBSCRIPTIONS[topic])}")
    await websocket.send(json.dumps({"type": "ack_subscribe", "topic": topic, "message": f"Successfully subscribed to {topic}"}))

async def unsubscribe_client_from_topic(websocket, topic: str):
    if topic in TOPIC_SUBSCRIPTIONS and websocket in TOPIC_SUBSCRIPTIONS[topic]:
        TOPIC_SUBSCRIPTIONS[topic].remove(websocket)
        CLIENT_TOPICS[websocket].discard(topic)
        print(f"Client {websocket.remote_address} UNSUBSCRIBED from topic: '{topic}'. Subscribers for '{topic}': {len(TOPIC_SUBSCRIPTIONS[topic])}")
        if not TOPIC_SUBSCRIPTIONS[topic]:
            del TOPIC_SUBSCRIPTIONS[topic]
            print(f"Topic '{topic}' has no more subscribers and was removed.")
        await websocket.send(json.dumps({"type": "ack_unsubscribe", "topic": topic, "message": f"Successfully unsubscribed from {topic}"}))
    else:
        print(f"Client {websocket.remote_address} tried to unsubscribe from '{topic}' but was not subscribed.")
        await websocket.send(json.dumps({"type": "error", "message": f"Not subscribed to {topic}"}))


async def send_to_topic(topic: str, message: str):
    """
    Sends a message to all clients subscribed to a specific topic.
    This is used for broadcasting data messages.
    """
    if topic not in TOPIC_SUBSCRIPTIONS or not TOPIC_SUBSCRIPTIONS[topic]:
        return

    tasks = []
    for client in list(TOPIC_SUBSCRIPTIONS[topic]):
        async def send_single_message(ws_client):
            try:
                await ws_client.send(message)
            except websockets.exceptions.ConnectionClosedOK:
                print(f"Client {ws_client.remote_address} closed connection during send to topic '{topic}'. Removing from subscriptions.")
                # Attempt to unregister this client immediately if it closed
                # This helps prevent further attempts to send to a dead connection
                await unregister_client(ws_client)
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"Client {ws_client.remote_address} connection error during send to topic '{topic}': {e}. Removing from subscriptions.")
                await unregister_client(ws_client)
            except Exception as e:
                print(f"Unexpected error sending to client {ws_client.remote_address} for topic '{topic}': {e}")
                # Consider unregistering for unexpected errors as well
                await unregister_client(ws_client)

        tasks.append(asyncio.create_task(send_single_message(client)))

    if tasks:
        # Wait for all tasks to complete. return_exceptions=True prevents gather from raising
        # an exception if any individual task fails, allowing others to complete.
        await asyncio.gather(*tasks, return_exceptions=True)


async def handler(websocket):
    """
    Handles a single WebSocket connection.
    Parses incoming messages for commands (subscribe/unsubscribe) or data.
    """
    await register_client(websocket)
    try:
        async for raw_message in websocket:
            print(f"DEBUG: Raw message received from {websocket.remote_address}: {raw_message[:100]}...")
            try:
                message = json.loads(raw_message)
                msg_type = message.get("type")
                topic = message.get("topic")

                if msg_type == "subscribe" and topic:
                    await subscribe_client_to_topic(websocket, topic)
                elif msg_type == "unsubscribe" and topic:
                    await unsubscribe_client_from_topic(websocket, topic)
                elif topic and "data" in message: # This is a data message for a specific topic (from producer)
                    print(f"DEBUG: Relaying data for topic '{topic}' from producer.")
                    # Ensure the 'data' part is sent as a JSON string
                    await send_to_topic(topic, json.dumps(message["data"]))
                else:
                    print(f"Received unknown or malformed message from {websocket.remote_address}: {raw_message}")
                    await websocket.send(json.dumps({"type": "error", "message": "Malformed message or unknown type. Expected {'type': 'subscribe/unsubscribe', 'topic': '...' } or {'topic': '...', 'data': {...}}"}))

            except json.JSONDecodeError:
                print(f"Received non-JSON message from {websocket.remote_address}: {raw_message}")
                await websocket.send(json.dumps({"type": "error", "message": "Message must be valid JSON."}))
            except Exception as e:
                print(f"Error processing message from {websocket.remote_address}: {e}")
                await websocket.send(json.dumps({"type": "error", "message": f"Server error processing message: {e}"}))

    except websockets.exceptions.ConnectionClosedOK:
        print(f"Connection closed cleanly by {websocket.remote_address}")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed with error by {websocket.remote_address}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred with client {websocket.remote_address}: {e}")
    finally:
        await unregister_client(websocket)

async def main():
    """Starts the WebSocket server."""
    print(f"Starting Python WebSocket server on port {WS_PORT}...")
    async with websockets.serve(handler, "0.0.0.0", WS_PORT):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
