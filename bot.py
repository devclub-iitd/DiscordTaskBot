import discord
import datetime
from tinydb import TinyDB, Query
from dotenv import load_dotenv
import os

print('started', flush=True)

load_dotenv()

if not os.path.exists('/db'):
    os.makedirs('/db')

db = TinyDB('/db/db.json')
# db = TinyDB('./db.json')
Msg = Query()

emojis = {
    'a': '🇦',
    'b': '🇧',
    'c': '🇨',
    'd': '🇩',
    'e': '🇪',
    'f': '🇫',
    'g': '🇬',
    'h': '🇭',
    'i': '🇮',
    'j': '🇯',
    'k': '🇰',
    'l': '🇱',
    'm': '🇲',
    'n': '🇳',
    'o': '🇴',
    'p': '🇵',
    'q': '🇶',
    'r': '🇷',
    's': '🇸',
    't': '🇹',
    'u': '🇺',
    'v': '🇻',
    'w': '🇼',
    'x': '🇽',
    'y': '🇾',
    'z': '🇿'
}

emoji_to_index = {}

for i, key in enumerate(emojis):
    emoji_to_index[emojis[key]] = i


class MyClient(discord.Client):
    async def _embed_msg(self, message):
        msg = message.content
        to_save = {'title': '', 'tasks': [], 'done': [], 'react': [], 'by': []}

        title_fileds = msg.split("{")[1].split("}")

        title = title_fileds[0].strip()
        to_save['title'] = title
        fields = title_fileds[1].split(",")

        modified_fields = ""
        val = 'a'
        reactions = []
        for _, text in enumerate(fields):
            modified_fields += f"{emojis[val]} "+text.strip()
            reactions.append(emojis[val])
            modified_fields += '\n'

            to_save['tasks'].append(text.strip())
            to_save['done'].append(False)
            to_save['react'].append(emojis[val])
            to_save['by'].append('')

            val = chr(ord(val)+1)

        embed = discord.Embed(colour=discord.Colour(
            0xc555f4), timestamp=datetime.datetime.utcnow())

        embed.add_field(name=title, value=modified_fields)
        return embed, reactions, to_save

    async def recreate_embed(self, data):
        embed = discord.Embed(colour=discord.Colour(
            0xc555f4), timestamp=datetime.datetime.utcnow())

        modified_fields = ""
        val = 'a'
        for i, task in enumerate(data['tasks']):
            done = data['done'][i]
            by = data['by'][i]

            if done:
                modified_fields += f"{emojis[val]} "+'~~'+task.strip()+'~~'
                modified_fields += ' (Completed by ' + by + ' )'
            else:
                modified_fields += f"{emojis[val]} "+task.strip()

            val = chr(ord(val)+1)
            modified_fields += '\n'

        embed.add_field(name=data['title'], value=modified_fields)
        return embed

    async def react(self, embed_msg, reaction):
        await embed_msg.add_reaction(emoji=reaction)

    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user), flush=True)

    async def on_message(self, message):
        content = message.content
        if content[:3] == '!tt':
            async with message.channel.typing():
                embed, reactions, to_save = await self._embed_msg(message)
                embed_msg = await message.channel.send(embed=embed)
                to_save['msg_id'] = embed_msg.id
                db.insert(to_save)

                for reaction in reactions:
                    await self.react(embed_msg, reaction)

    async def on_raw_reaction_add(self, payload):
        if(payload.user_id == self.user.id):
            return

        res = db.search(Msg.msg_id == payload.message_id)

        if len(res) != 0:
            saved_data = res[0]
            user_id = payload.user_id
            message_id = payload.message_id
            emoji = payload.emoji
            if str(emoji) not in saved_data['react']:
                return
            else:
                index = emoji_to_index[str(emoji)]
                channel = self.get_channel(payload.channel_id)
                msg = await channel.fetch_message(message_id)
                if saved_data['done'][index]:
                    embed = await self.recreate_embed(saved_data)
                    if msg.embeds[0] != embed:
                        await msg.edit(embed=embed)
                    else:
                        return
                else:
                    saved_data['done'][index] = True
                    user = self.get_user(user_id).mention
                    saved_data['by'][index] = str(user)
                    db.upsert(saved_data, Msg.msg_id == message_id)
                    embed = await self.recreate_embed(saved_data)
                    await msg.edit(embed=embed)

    async def on_raw_reaction_remove(self, payload):
        res = db.search(Msg.msg_id == payload.message_id)

        if len(res) != 0:
            saved_data = res[0]
            # user_id = payload.user_id
            message_id = payload.message_id
            emoji = payload.emoji
            if str(emoji) not in saved_data['react']:
                return
            else:
                index = emoji_to_index[str(emoji)]
                channel = self.get_channel(payload.channel_id)
                msg = await channel.fetch_message(message_id)

                if not saved_data['done'][index]:
                    embed = await self.recreate_embed(saved_data)
                    if msg.embeds[0] != embed:
                        await msg.edit(embed=embed)
                    else:
                        return
                else:
                    count = 0
                    for reaction in msg.reactions:
                        if str(reaction.emoji) == str(emoji):
                            count = reaction.count - 1
                            break
                    if count == 0:
                        saved_data['done'][index] = False
                        saved_data['by'][index] = ''
                        db.upsert(saved_data, Msg.msg_id == message_id)
                        embed = await self.recreate_embed(saved_data)
                        await msg.edit(embed=embed)
                    else:
                        return


client = MyClient()
client.run(os.getenv("TOKEN"))
