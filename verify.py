import asyncio
import json
import time
import discord
import requests
from discord.ext import commands
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(intents=intents)

CLIENT_ID = 'YOUR CLIENT ID'
CLIENT_SECRET = 'YOUR CLIENT SECRET'
REDIRECT_URI = 'https://api.cometbot.info/discord/callback' # CHANGE THIS TO YOUR DOMAIN OBV
GUILD_ID = 'GUILD ID'
BOT_TOKEN = 'BOT TOKEN'
role_id = '' # ROLE TO GIVE MEMBERS THAT GET RESTORED.
owners = [1014608783244275744, 1064935195914010664] # PUT OWNER IDS HERE, OWNERS ARE PEOPLE THAT CAN DO THE RESTORE COMMAND!


def refresh_access_token(refresh_token):
    token_response = requests.post('https://discord.com/api/oauth2/token', data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'scope': 'identify guilds.join'
    }, headers={
        'Content-Type': 'application/x-www-form-urlencoded'
    })

    if token_response.status_code == 200:
        new_access_token = token_response.json().get('access_token')
        new_refresh_token = token_response.json().get('refresh_token')
        return new_access_token, new_refresh_token
    else:
        print(f"Error refreshing access token: {token_response.json()}")
        return None, None


def load_user_data():
    with open("/root/API/users.json", "r") as infile: # CHANGE PATH TO YOUR JSON FOLDER!
        return json.load(infile)


def save_user_data(data):
    with open(f"/root/API/users.json", "w") as infile: #CHANGE PATH TO YOUR JSON FOLDER!
        return json.dump(data, infile)


def is_token_expired(expiration_timestamp):
    return int(time.time()) >= expiration_timestamp


@bot.slash_command(name="restore", description="Restores our users")
async def restore(ctx):
    if ctx.author.id in owners:
        await ctx.respond('Restoring users!', ephemeral=True)
        user_data_dict = load_user_data()
        for username, user_data in user_data_dict.items():
            if 'discord' in user_data:
                if is_token_expired(user_data['expiration_timestamp']):
                    new_access_token, new_refresh_token = refresh_access_token(user_data['refresh_token'])
                    if new_access_token and new_refresh_token:
                        user_data['access_token'] = new_access_token
                        user_data['refresh_token'] = new_refresh_token
                        user_data['expiration_timestamp'] = int(time.time()) + 3600
                        save_user_data(user_data)

                add_member_url = f'https://discord.com/api/guilds/{ctx.guild.id}/members/{user_data["id"]}'
                add_member_headers = {
                    'Authorization': f'Bot {BOT_TOKEN}',
                    'Content-Type': 'application/json'
                }
                add_member_data = {
                    'access_token': user_data['access_token'],
                    'roles': [{role_id}]
                }

                add_member_result = requests.put(add_member_url, json=add_member_data, headers=add_member_headers)
                print(add_member_result.status_code)
                await asyncio.sleep(2)

    else:
        await ctx.respond('Only Owners Can Use This!')


bot.run(BOT_TOKEN)
