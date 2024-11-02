from telethon import TelegramClient, events
from telethon.tl.custom import Button
import csv
import os

# Replace these with your own values
api_id = '21078554'  # Your API ID
api_hash = 'fca31798b27a1010122a0ab57e9fdf63'  # Your API Hash
bot_token = '7691240319:AAH2oAzWPr4uDKRTow8iS7SwHMCK-ubh17c'  # Your bot token

# Create the client and connect
client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)

# Global variables for filter words and usernames
filter_words = []
replacement_words = []
source_group_usernames = []  # Changed to a list for multiple source groups
target_group_username = None  # Single target group
processed_message_ids = set()  # Set to track processed message IDs

# Define the command handler for the /start command
@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await event.respond(
        'Welcome! Please choose an option:',
        buttons=[
            [Button.inline("Start Listening", b'button1')],
            [Button.inline("Add Filter Word", b'add_filter')],
            [Button.inline("Button 3", b'button3')],
            [Button.inline("Button 4", b'button4')]
        ]
    )

# Define the callback handler for button clicks
@client.on(events.CallbackQuery)
async def button_click_handler(event):
    if event.data == b'button1':
        await event.answer('Listening for messages...')
        await load_usernames_from_csv()  # Load usernames from CSV
        await start_listening()  # Start listening for messages
        await event.respond(f"Listening for messages in the source groups: {', '.join(source_group_usernames)}")
    elif event.data == b'add_filter':
        await event.answer('Please send the filter word in the format: filter_word=replacement_word')
    elif event.data == b'button3':
        await event.answer('You clicked Button 3!')
    elif event.data == b'button4':
        await event.answer('You clicked Button 4!')
    else:
        await event.answer('Unknown button clicked.')

# Handle incoming messages for adding filter words
@client.on(events.NewMessage)
async def add_filter_handler(event):
    # Check if the message is a response to the add_filter button
    if event.message.message and not event.message.from_id == (await client.get_me()).id:
        if '=' in event.message.message:
            try:
                # Extract filter word and replacement word
                filter_word, replacement_word = map(str.strip, event.message.message.split('=', 1))

                # Update global filter word lists
                filter_words.append(filter_word)
                replacement_words.append(replacement_word)

                # Write to the CSV file
                await write_to_csv_file()

                await event.respond(f'✅ Added filter: "{filter_word}" with replacement: "{replacement_word}"')
            except Exception as e:
                await event.respond(f'❌ Error processing command: {e}')

# Functions to handle CSV operations
async def write_to_csv_file():
    global filter_words, replacement_words
    try:
        with open('filter_replacement.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            for filter_word, replacement_word in zip(filter_words, replacement_words):
                writer.writerow([filter_word, replacement_word])
        print("Filter and replacement words written to CSV file successfully.")
    except Exception as e:
        print(f"Error writing to CSV file: {e}")

async def load_usernames_from_csv():
    global source_group_usernames, target_group_username
    try:
        if os.path.exists('usernames.csv'):
            with open('usernames.csv', 'r') as file:
                reader = csv.reader(file)
                source_group_usernames = [username.strip() for username in next(reader)]  # Load source usernames
                target_group_username = next(reader)[0].strip()  # Load the single target username
                print("User names loaded from CSV file successfully.")
    except Exception as e:
        print(f"Error loading usernames from CSV file: {e}")

async def start_listening ():
    if source_group_usernames and target_group_username:
        for source_group in source_group_usernames:
            client.add_event_handler(my_event_handler, events.NewMessage(chats=source_group))
        print(f"Listening for messages in the source groups: {', '.join(source_group_usernames)}")

async def my_event_handler(event):
    if not event.message:
        return

    if event.message.id in processed_message_ids:
        return  # Skip if the message has already been processed

    original_message = event.message.message
    media = event.message.media

    # Replace all filter words with their corresponding replacement words
    modified_message = original_message
    for filter_word, replacement_word in zip(filter_words, replacement_words):
        modified_message = modified_message.replace(filter_word, replacement_word)

    try:
        if media:
            await client.send_file(target_group_username, media, caption=modified_message)
            print(f"Media file and modified caption sent to target group {target_group_username} successfully.")
        else:
            await client.send_message(target_group_username, modified_message)
            print(f"Modified message sent to target group {target_group_username} successfully.")
        processed_message_ids.add(event.message.id)  # Add the message ID to the set
    except Exception as e:
        print(f"Error: {e}")

# Start the bot
async def main():
    print("Bot is running...")
    await client.start()
    await client.run_until_disconnected()

# Run the bot
with client:
    client.loop.run_until_complete(main())