#!/bin/bash

# ==========================
# WhatsApp Messages Module
# ==========================

mkdir -p src/messages/{chats,audios,images,videos,documents,interactions,reactions}

# Root files
touch src/messages/__init__.py
touch src/messages/webhook.py
touch src/messages/parser.py
touch src/messages/router.py
touch src/messages/sender.py
touch src/messages/downloader.py
touch src/messages/validator.py

# Chats
touch src/messages/chats/__init__.py
touch src/messages/chats/text_handler.py
touch src/messages/chats/command_handler.py
touch src/messages/chats/conversation.py

# Audios
touch src/messages/audios/__init__.py
touch src/messages/audios/audio_handler.py
touch src/messages/audios/transcriber.py
touch src/messages/audios/tts.py

# Images
touch src/messages/images/__init__.py
touch src/messages/images/image_handler.py
touch src/messages/images/image_processor.py

# Videos
touch src/messages/videos/__init__.py
touch src/messages/videos/video_handler.py
touch src/messages/videos/video_processor.py

# Documents
touch src/messages/documents/__init__.py
touch src/messages/documents/document_handler.py
touch src/messages/documents/extractor.py

# Interactions
touch src/messages/interactions/__init__.py
touch src/messages/interactions/interactive_handler.py
touch src/messages/interactions/button_handler.py
touch src/messages/interactions/list_handler.py
touch src/messages/interactions/flow_handler.py

# Reactions
touch src/messages/reactions/__init__.py
touch src/messages/reactions/reaction_handler.py

echo "✅ WhatsApp messages module scaffolded."