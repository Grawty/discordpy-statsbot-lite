import discord
from discord.ext import tasks
import requests
import asyncio
from dotenv import load_dotenv
import os
load_dotenv()

intents = discord.Intents.default()
intents.members = True

TOKEN = os.getenv("TOKEN") #  .env.example
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID"))

client = discord.Client(intents=intents)

async def abone_sayisini_guncelle():
    await client.wait_until_ready()
    kanal = client.get_channel(VOICE_CHANNEL_ID)
    while not client.is_closed():
        abone_sayisi = abone_sayisini_sonuc()
        await kanal_ismi_guncelle(kanal, abone_sayisi)
        await asyncio.sleep(350)

def abone_sayisini_sonuc():
    url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={YOUTUBE_CHANNEL_ID}&key={YOUTUBE_API_KEY}"
    cevap = requests.get(url)
    veri = cevap.json()
    abone_sayisi = veri['items'][0]['statistics']['subscriberCount']
    return abone_sayisi

async def kanal_ismi_guncelle(kanal, sayi):
    await kanal.edit(name=f"YouTube: {sayi} ♥")

async def youtube_goruntulenme_guncelle():
    await client.wait_until_ready()
    while not client.is_closed():
        toplam_goruntulenme = youtube_toplam_goruntulenme_sonuc()
        await asyncio.sleep(3600)
        aktivite = discord.Activity(type=discord.ActivityType.playing, name=f"Toplam Görüntülenme: {toplam_goruntulenme}")
        await client.change_presence(activity=aktivite)

def youtube_toplam_goruntulenme_sonuc():
    url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={YOUTUBE_CHANNEL_ID}&key={YOUTUBE_API_KEY}"
    cevap = requests.get(url)
    veri = cevap.json()
    toplam_goruntulenme = veri['items'][0]['statistics']['viewCount']
    return toplam_goruntulenme

def en_son_video_basligini_sonuc():
    url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={YOUTUBE_CHANNEL_ID}&order=date&part=snippet&type=video&maxResults=1"
    cevap = requests.get(url)
    veri = cevap.json()
    en_son_video_basligi = veri['items'][0]['snippet']['title']
    return en_son_video_basligi


async def aktiviteleri_guncelle():
    while True:
        abone_sayisi = abone_sayisini_sonuc()
        toplam_goruntulenme = youtube_toplam_goruntulenme_sonuc()
        en_son_video_basligi = en_son_video_basligini_sonuc()
        

        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=f"Discord {sum(guild.member_count for guild in client.guilds)} üye 🦄"))
        await asyncio.sleep(20) # ne kadar süre gösterileceğini ayarlar.

        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{toplam_goruntulenme} görüntülenme 🙌"))
        await asyncio.sleep(20)

        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{abone_sayisi} abone 🥳"))
        await asyncio.sleep(20)

        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"En Son Video: {en_son_video_basligi}"))
        await asyncio.sleep(20)

            
                
       
@client.event
async def on_ready():
    print(f'Hazır - {client.user}')

    client.loop.create_task(aktiviteleri_guncelle())
    client.loop.create_task(youtube_goruntulenme_guncelle())

    ses_kanali = client.get_channel(VOICE_CHANNEL_ID)
    if ses_kanali:
        try:
            await ses_kanali.connect()
        except RuntimeError as e:
            print(f"Ses kanalına bağlanılamadı: {e}")
    else:
        print("Ses kanalı bulunamadı.")

    client.loop.create_task(abone_sayisini_guncelle())

client.run(TOKEN)
