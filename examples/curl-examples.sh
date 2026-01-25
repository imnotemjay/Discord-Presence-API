#!/bin/bash

# Discord Presence API - cURL Examples
# Replace YOUR_BOT_TOKEN with your actual Discord bot token
# Replace USER_ID with the target Discord user ID

BOT_TOKEN="YOUR_BOT_TOKEN"
USER_ID="1456392490566287529"
BASE_URL="http://localhost:3000/v1"

echo "=== Discord Presence API Examples ==="
echo

# Health Check
echo "1. Health Check:"
curl -s "${BASE_URL}/health" | jq '.'
echo
echo

# Get User Profile
echo "2. Get User Profile:"
curl -s -H "Authorization: Bot ${BOT_TOKEN}" "${BASE_URL}/users/${USER_ID}" | jq '.'
echo
echo

# Get User Presence
echo "3. Get User Presence:"
curl -s -H "Authorization: Bot ${BOT_TOKEN}" "${BASE_URL}/presence/${USER_ID}" | jq '.'
echo
echo

# Get User Presence with Guild ID
echo "4. Get User Presence with Guild ID:"
GUILD_ID="YOUR_GUILD_ID"
curl -s -H "Authorization: Bot ${BOT_TOKEN}" "${BASE_URL}/presence/${USER_ID}?guildId=${GUILD_ID}" | jq '.'
echo
echo

# Get Guilds
echo "5. Get Bot Guilds:"
curl -s -H "Authorization: Bot ${BOT_TOKEN}" "${BASE_URL}/guilds" | jq '.'
echo
echo

# Example with production URL
echo "6. Production Example (Render.com):"
PROD_URL="https://discord-presence-api.onrender.com/v1"
echo "curl -H \"Authorization: Bot ${BOT_TOKEN}\" \"${PROD_URL}/users/${USER_ID}\""
echo

echo "=== End Examples ==="
