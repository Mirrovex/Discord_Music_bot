prefix = '.m1 '

import discord
from discord.ext import commands
import asyncio.base_events
import youtube_dl
import random

intents = discord.Intents.all()
discord.member = True

client = commands.Bot(command_prefix = prefix, intents=intents)

last_message = None
voice = None
queue_list = []
titles = []
now_play = 0
loop_one = False
#shuffle = False
stop_user_id = []

@client.event
async def on_raw_reaction_remove(payload):
    global stop_user_id
    global voice
    if payload.message_id == last_message.id and payload.emoji.name == '⏯' and voice.is_paused:
        for i in stop_user_id:
            await last_message.remove_reaction('⏯', i)
        stop_user_id.clear()
        voice.resume()

def update_embed():
    global loop_one
    #global shuffle

    newEmbed = discord.Embed(title='Music Bot :)', description='', color=0x3498db)
    newEmbed.add_field(name = "Opcje:", value = f"loop_one = {loop_one}", inline=False)
    #newEmbed.set_footer(text = f"Opcje: loop_one = {loop_one}, shuffle = {shuffle}")

    return newEmbed

def play_next(error = None, value = ''):
    global now_play
    global loop_one
    #global shuffle
            
    if voice != None and voice.is_playing:
        voice.pause()

    if value == '' and loop_one == False:
        value = '+'

    if value == '-':
        now_play -= 1
    elif value == '+':
        now_play += 1

    if now_play > len(queue_list) - 1:
        now_play = 0
    elif now_play < 0:
        now_play = len(queue_list) - 1
    
    ffmpeg_opts = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'} #ponowne laczenie
    ydl_opts = {'format': 'bestaudio'}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(queue_list[now_play], download=False) #tylko odtwarzanie (bez pobierania na pc)
        URL = info['formats'][0]['url']
    voice.play(discord.FFmpegPCMAudio(URL, **ffmpeg_opts), after = play_next) #puszczanie muzyki


@client.event
async def on_raw_reaction_add(payload):
    global voice
    global stop_user_id
    global loop_one
    #global shuffle
    global last_message
    global queue_list
    global titles
    global now_play

    if payload.member.bot:
        pass

    elif last_message != None:
        if payload.message_id == last_message.id:
            if payload.emoji.name == '⏯' and voice != None and voice.is_playing:
                stop_user_id.append(payload.member)
                voice.pause()

            elif payload.emoji.name == '⬅': #poprzednia
                await last_message.remove_reaction('⬅', payload.member)
                for i in stop_user_id:
                    await last_message.remove_reaction('⏯', i)
                stop_user_id.clear()
                play_next('', '-')

            elif payload.emoji.name == '➡': #nastepna
                await last_message.remove_reaction('➡', payload.member)
                for i in stop_user_id:
                    await last_message.remove_reaction('⏯', i)
                stop_user_id.clear()
                play_next('', '+')

            elif payload.emoji.name == '🔂':
                await last_message.remove_reaction('🔂', payload.member)
                loop_one = not loop_one
                newEmbed = update_embed()
                await last_message.edit(embed=newEmbed)

            elif  payload.emoji.name == '🔀':
                await last_message.remove_reaction('🔀', payload.member)
                #shuffle = not shuffle
                #newEmbed = update_embed()
                #await last_message.edit(embed=newEmbed)

                now_play_url = queue_list[now_play]

                all_list = list(zip(queue_list, titles))
                random.shuffle(all_list)
                queue_list, titles = zip(*all_list)
                queue_list = list(queue_list)
                titles = list(titles)

                now_play = queue_list.index(now_play_url)
            
            elif payload.emoji.name == '❌':
                await last_message.remove_reaction('❌', payload.member)
                await last_message.delete()
                last_message = None
                if voice.is_playing:
                    voice.pause()
                await voice.disconnect()

                queue_list.clear()
                titles.clear()

                voice = None



@client.event
async def on_ready():
    print('Bot jest gotowy')
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name = str(prefix)))

"""@client.command(pass_context = True)
async def m(ctx, cmd1 = '', url=''):
    global last_message
    global voice
    global now_play
    global loop_one
    #global shuffle"""

@client.command(name = 'play', help = 'Puszczanie muzyki z linku lub numeru w kolejce')
async def play(ctx, url=''): #mozna puszczac url i numer z kolejki
    global last_message
    global voice
    global now_play

    try:
        url = int(url)
        if len(queue_list) >= 1:
            if url > len(queue_list):
                url = len(queue_list) - 1
            elif url < 1:
                url = 0
            else:
                url -= 1
        else:
            url = ''
    except:
        pass

    try:
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        voice.pause()
    except:
        channel = ctx.author.voice.channel
        await channel.connect() #podlaczenie do czatu glosowego

    if url != '': #puszczanie muzyki z youtube
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

        if isinstance(url, str):
            queue_list.append(url)
            now_play = len(queue_list) - 1
        else:
            now_play = url

        ffmpeg_opts = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'} #ponowne laczenie
        ydl_opts = {'format': 'bestaudio'}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(queue_list[now_play], download=False) #tylko odtwarzanie (bez pobierania na pc)
            video_title = info.get('title', None) #pobieranie tytulu filmiku
            URL = info['formats'][0]['url']
        voice.play(discord.FFmpegPCMAudio(URL, **ffmpeg_opts), after = play_next) #puszczanie muzyki

        if isinstance(url, str):
            titles.append(video_title)

        if last_message != None:
            await last_message.delete()

        newEmbed = update_embed()
        last_message = await ctx.send(embed=newEmbed)

        await last_message.add_reaction('⬅')
        await last_message.add_reaction('⏯')
        await last_message.add_reaction('➡')
        await last_message.add_reaction('🔂')
        await last_message.add_reaction('🔀')
        await last_message.add_reaction('❌')


"""@client.command(name = 'leave', help = 'Usuwanie bota z kanału')
async def leave(ctx):
    global voice

    await ctx.message.add_reaction('✅')
    if voice.is_playing:
        voice.pause()
    await voice.disconnect()
    voice = None"""


@client.command(name = 'add', help = 'Dodawanie piosenki do kolejki')
async def add(ctx, url = ''):
    global voice

    await ctx.message.add_reaction('✅')
    queue_list.append(url)

    ydl_opts = {'format': 'bestaudio'}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl: #tytul muzyki
        info = ydl.extract_info(url, download=False) #tylko odtwarzanie (bez pobierania na pc)
        title = info.get('title', None) #pobieranie tytulu filmiku

    titles.append(title)

    if voice != None:
        newEmbed = update_embed()
        last_message = await ctx.send(embed=newEmbed)

        await last_message.add_reaction('⬅')
        await last_message.add_reaction('⏯')
        await last_message.add_reaction('➡')
        await last_message.add_reaction('🔂')
        await last_message.add_reaction('🔀')
        await last_message.add_reaction('❌')


@client.command(name = 'delete', help = 'Usuwanie piosenki z kolejki za pomocą numeru lub linku')
async def delete(ctx, url = ''):
    global voice

    await ctx.message.add_reaction('✅')
    try:
        url = int(url)
    except:
        pass
    for link in range(len(queue_list)):
        if queue_list[link] == url or link + 1 == url:
            queue_list.remove(queue_list[link])
            titles.remove(titles[link])
        
    if len(queue_list) == 0:
        voice.pause()
        await voice.disconnect()
        voice = None

    if voice != None:
        newEmbed = update_embed()
        last_message = await ctx.send(embed=newEmbed)

        await last_message.add_reaction('⬅')
        await last_message.add_reaction('⏯')
        await last_message.add_reaction('➡')
        await last_message.add_reaction('🔂')
        await last_message.add_reaction('🔀')
        await last_message.add_reaction('❌')
        
@client.command(name = 'clear', help = 'Wyczyszczenie kolejki')
async def clear(ctx):
    global voice

    await ctx.message.add_reaction('✅')
    queue_list.clear()
    titles.clear()

    voice.pause()
    await voice.disconnect()
    voice = None


@client.command(name = 'queue', help = 'Wyświetlanie kolejki')
async def queue(ctx, url = ''):
    global last_message
    global voice
    global now_play

    msg = ''

    for title in range(len(titles)):
        if title == now_play:
            msg += str(title + 1) + '. 🔊 ' + str(titles[title]) + '\n'
        else:
            msg += str(title + 1) + '. ' + str(titles[title]) + '\n'

    newEmbed = discord.Embed(title='Kolejka: ', description=msg, color=0x3498db)
    await ctx.send(embed=newEmbed)

    if last_message != None:
        await last_message.delete()

    if voice != None:
        newEmbed = update_embed()
        last_message = await ctx.send(embed=newEmbed)

        await last_message.add_reaction('⬅')
        await last_message.add_reaction('⏯')
        await last_message.add_reaction('➡')
        await last_message.add_reaction('🔂')
        await last_message.add_reaction('🔀')
        await last_message.add_reaction('❌')

"""elif cmd1 == 'preset' or cmd1 == 'skrot':
    pass

elif cmd1 == 'presets' or cmd1 == 'skroty':
    pass"""


client.run('TOKEN')
