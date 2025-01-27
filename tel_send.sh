#!/bin/bash

TELEGRAM_BOT_TOKEN=7634942101:AAHZJCtwV08CINmDidnmn7MfQLpP4GtHcu8
mids="$(curl -s https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getUpdates | jq -r '.result[].message.chat.id' | uniq)" 
msg="$1"
for i in $mids; do
	data="{\"chat_id\":\"$i\",\"text\":\"$msg\",\"disable_notification\": true}"
	curl -s -o /dev/null -X POST \
     		-H 'Content-Type: application/json' \
		-d "$data" \
		https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage	
done
