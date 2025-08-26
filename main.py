import os 
import discord
import requests
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import random
import json
import time
import asyncio

load_dotenv()
TOKEN = os.getenv("TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
API_R = os.getenv("API_KEY_R")
gatos = [gato for gato in os.listdir("./gatos") if gato.endswith(".png")]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"{bot.user} has connected to Discord!")
    
    
@bot.event
async def on_join(msg):
    msg.channel.send(f"Gay quien lo lea, mas gay quien siga leyendo, y ultra gay quien lea hasta aqui\n(excepto el dueño del bot, que es un crack y Valentin que ya no puede ser mas margarito)")

@bot.tree.command(name="duelo", description="Reta a otro usuario a un duelo (debes usar @ para seleccionarlo)", guild=discord.Object(id=GUILD_ID))
async def duelo(interaction: discord.Interaction, persona_a_retar: str):
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("No se pudo encontrar el servidor.")
        return
    # Solo buscar si es una mención válida
    user_id = None
    if persona_a_retar.startswith('<@') and persona_a_retar.endswith('>'):
        persona_a_retar = persona_a_retar.replace('<@', '').replace('!', '').replace('>', '')
        if persona_a_retar.isdigit():
            user_id = int(persona_a_retar)
    if user_id:
        member = guild.get_member(user_id)
        if member:
            with open("marcadores.json","r") as f:
                datos = json.load(f)
            if datos["duelo_activo"]:
                await interaction.response.send_message("***Ya hay un duelo activo*** \nLos participantes pueden cancelar el duelo cuando quieran usando /cancelar_duelo \nSi el duelo lleva mas de 1h 30min activo todos pueden cancelarlo usando /cancelar_duelo")
                return
            else:
                datos["participante1"] = interaction.user.id
                datos["participante2"] = member.id
                with open("marcadores.json","w+") as f:
                    json.dump(datos,f,indent=4)
                await interaction.response.send_message(f"__**{interaction.user.mention} ha retado a {member.mention} a un duelo!**__ \n\n *{member.mention} puedes aceptar el duelo usando /aceptar_duelo*")
                return
    else:
        await interaction.response.send_message("Debes mencionar a un usuario válido usando @.")

@bot.tree.command(name="aceptar_duelo",description="Acepta el duelo al que has sido desafiado",guild=discord.Object(id=GUILD_ID))
async def aceptar_duelo(interaction: discord.Interaction):
    guild = interaction.guild
    with open("marcadores.json","r") as f:    
        datos = json.load(f)
    if datos["participante2"] != interaction.user.id:
        await interaction.response.send_message(f"{interaction.user.mention}, ¿Qué hacer payaso? Que a ti no te han retado SUBNORMAL, **Aprende a leer**")
    elif datos["duelo_activo"]:
        await interaction.response.send_message(f"{interaction.user.mention} tiene alzheimer, se ha olvidado de que ya ha aceptado el duelo")
    else:
        datos["duelo_activo"] = True
        datos["hora_activacion"] = time.time() #tiempo desde 1970 en segundos
        with open("marcadores.json","w+") as f:
            json.dump(datos,f,indent=4)
        await interaction.response.send_message(f"**__{(guild.get_member(datos["participante2"]).mention).capitalize()} ha aceptado el reto de {(guild.get_member(datos["participante1"]).mention).capitalize()}!!!!!__**")
            

@bot.tree.command(name="cancelar_duelo",description="Cancela el duelo activo",guild=discord.Object(id=GUILD_ID))
async def cancelar_duelo(interaction: discord.Interaction):
    guild = interaction.guild
    with open("marcadores.json","r") as f:
        datos = json.load(f)
    tiempo_restante = (int(datos["hora_activacion"]) - time.time()) // 60
    if not datos["duelo_activo"]:
        await interaction.response.send_message("No hay un duelo activo para cancelar, puedes crear uno usando /duelo",ephemeral=True)
    elif (interaction.user.id != datos["participante1"] and interaction.user.id != datos["participante2"]) and tiempo_restante <= 90:
        await interaction.response.send_message(f"Todavia no ha pasado el tiempo necesario para cancelar un duelo ajeno\n Tiempo transcurrido: {tiempo_restante} minutos",ephemeral=True)
    else:
        participante1 = guild.get_member(datos["participante1"])
        participante2 = guild.get_member(datos["participante2"])
        m1 = participante1.mention if participante1 else str(datos["participante1"])
        m2 = participante2.mention if participante2 else str(datos["participante2"])
        frase = f"El duelo entre {m1} y {m2} ha sido cancelado"
        datos["participante1"] = ""
        datos["participante2"] = ""
        datos["duelo_activo"] = False
        datos["hora_activacion"] = 0
        with open("marcadores.json","w+") as f:
            json.dump(datos,f,indent=4)
        await interaction.response.send_message(frase)
        
@bot.tree.command(name="duelo_ganado", description="Termina el duelo y te declara como el ganador", guild=discord.Object(id=GUILD_ID))
async def duelo_ganado(interaction: discord.Interaction):
    with open("marcadores.json", "r") as f:
        datos = json.load(f)
    if not datos["duelo_activo"]:
        await interaction.response.send_message("No hay un duelo activo actualmente\nUsa */duelo* para retar a alguien", ephemeral=True)
    elif not datos["participante1"] or not datos["participante2"]:
        await interaction.response.send_message("No hay un duelo activo actualmente\nUsa */duelo* para retar a alguien", ephemeral=True)
        return
    else:
        try:
            participante1_id = int(datos["participante1"])
            participante2_id = int(datos["participante2"])
        except ValueError:
            await interaction.response.send_message("Error: los participantes del duelo no son válidos. Usa */duelo* para iniciar uno nuevo.", ephemeral=True)
            return
        if interaction.user.id != participante1_id and interaction.user.id != participante2_id:
            await interaction.response.send_message("No puedes declararte ganador de un duelo en el que no participas", ephemeral=True)
            return
        user_id = str(interaction.user.id)
        # Determinar el perdedor (el que no es el usuario actual)
        if user_id == str(participante1_id):
            perdedor_id = str(participante2_id)
        else:
            perdedor_id = str(participante1_id)
        # Inicializar o actualizar datos del ganador
        if user_id not in datos:
            datos[user_id] = {"puntos": 1000, "nombre": interaction.user.display_name}
        else:
            # Si no tiene nombre, añadirlo o actualizarlo si cambió
            if "nombre" not in datos[user_id] or datos[user_id]["nombre"] != interaction.user.display_name:
                datos[user_id]["nombre"] = interaction.user.display_name
        # Inicializar o actualizar datos del perdedor
        perdedor_member = interaction.guild.get_member(int(perdedor_id))
        perdedor_nombre = perdedor_member.display_name if perdedor_member else perdedor_id
        if perdedor_id not in datos:
            datos[perdedor_id] = {"puntos": 1000, "nombre": perdedor_nombre}
        else:
            if "nombre" not in datos[perdedor_id] or datos[perdedor_id]["nombre"] != perdedor_nombre:
                datos[perdedor_id]["nombre"] = perdedor_nombre
        # Sumar/restar puntos
        puntos_actuales_ganador = int(datos[user_id].get("puntos", 1000))
        puntos_actuales_perdedor = int(datos[perdedor_id].get("puntos", 1000))
        datos[user_id]["puntos"] = puntos_actuales_ganador + 50
        datos[perdedor_id]["puntos"] = puntos_actuales_perdedor - 50
        # Limpiar estado de duelo
        datos["participante1"] = ""
        datos["participante2"] = ""
        datos["duelo_activo"] = False
        datos["hora_activacion"] = 0
        with open("marcadores.json", "w") as f:
            json.dump(datos, f, indent=4)
        ment_perdedor = perdedor_member.mention if perdedor_member else perdedor_nombre
        await interaction.response.send_message(f"**{interaction.user.mention} le ha ganado a {ment_perdedor}**\nPuntuaciones:\n{interaction.user.mention} ({datos[user_id]['nombre']}) : {datos[user_id]['puntos']} puntos en total\n{ment_perdedor} ({datos[perdedor_id]['nombre']}) : {datos[perdedor_id]['puntos']} puntos en total")
        
@bot.tree.command(name="duelo_perdido",description="Termina el duelo y te declara como el perdedor", guild=discord.Object(id=GUILD_ID))
async def duelo_perdido(interaction: discord.Interaction):
    with open("marcadores.json", "r") as f:
        datos = json.load(f)
    if not datos["duelo_activo"]:
        await interaction.response.send_message("No hay un duelo activo actualmente\nUsa */duelo* para retar a alguien", ephemeral=True)
    elif not datos["participante1"] or not datos["participante2"]:
        await interaction.response.send_message("No hay un duelo activo actualmente\nUsa */duelo* para retar a alguien", ephemeral=True)
        return
    else:
        try:
            participante1_id = int(datos["participante1"])
            participante2_id = int(datos["participante2"])
        except ValueError:
            await interaction.response.send_message("Error: los participantes del duelo no son válidos. Usa */duelo* para iniciar uno nuevo.", ephemeral=True)
            return
        if interaction.user.id != participante1_id and interaction.user.id != participante2_id:
            await interaction.response.send_message("No puedes declararte ganador de un duelo en el que no participas", ephemeral=True)
            return
        user_id = str(interaction.user.id)
        # Determinar el ganador (el que no es el usuario actual)
        if user_id == str(participante1_id):
            ganador_id = str(participante2_id)
        else:
            ganador_id = str(participante1_id)
        # Inicializar o actualizar datos del ganador
        if user_id not in datos:
            datos[user_id] = {"puntos": 1000, "nombre": interaction.user.display_name}
        else:
            # Si no tiene nombre, añadirlo o actualizarlo si cambió
            if "nombre" not in datos[user_id] or datos[user_id]["nombre"] != interaction.user.display_name:
                datos[user_id]["nombre"] = interaction.user.display_name
        # Inicializar o actualizar datos del perdedor
        ganador_member = interaction.guild.get_member(int(ganador_id))
        ganador_nombre = ganador_member.display_name if ganador_member else ganador_id
        if ganador_id not in datos:
            datos[ganador_id] = {"puntos": 1000, "nombre": ganador_nombre}
        else:
            if "nombre" not in datos[ganador_id] or datos[ganador_id]["nombre"] != ganador_nombre:
                datos[ganador_id]["nombre"] = ganador_nombre
        # Sumar/restar puntos
        puntos_actuales_perdedor = int(datos[user_id].get("puntos", 1000))
        puntos_actuales_ganador = int(datos[ganador_id].get("puntos", 1000))
        datos[user_id]["puntos"] = puntos_actuales_perdedor - 50
        datos[ganador_id]["puntos"] = puntos_actuales_ganador + 50
        # Limpiar estado de duelo
        datos["participante1"] = ""
        datos["participante2"] = ""
        datos["duelo_activo"] = False
        datos["hora_activacion"] = 0
        with open("marcadores.json", "w") as f:
            json.dump(datos, f, indent=4)
        ment_ganador = ganador_member.mention if ganador_member else ganador_nombre
        await interaction.response.send_message(f"**{ment_ganador} le ha ganado a {interaction.user.mention}**\nPuntuaciones:\n{interaction.user.mention} ({datos[user_id]['nombre']}) : {datos[user_id]['puntos']} puntos en total\n{ment_ganador} ({datos[ganador_id]['nombre']}) : {datos[ganador_id]['puntos']} puntos en total")

@bot.tree.command(name="marcadores",description="Muestra los marcadores",guild=discord.Object(id=GUILD_ID))
async def marcadores(interaction: discord.Interaction):
    with open("marcadores.json","r") as f:
        datos = json.load(f)
    claves = datos.keys()
    claves_ids = [clave for clave in claves if clave.isdigit()]
    mensaje = ""
    for clave in claves_ids:
        mensaje += f"{interaction.guild.get_member(int(clave))} tiene : {datos[clave]["puntos"]} puntos\n"
    await interaction.response.send_message(mensaje)

@bot.tree.command(name="equipos", description="Crea 2 equipos aleatorios, introduce los participantes separados por ' '(espacio)", guild=discord.Object(id=GUILD_ID))
async def equipos(interaction: discord.Interaction, participantes: str):
    participantes = [p.strip().capitalize() for p in participantes.split(' ')]
    if len(participantes) < 2:
        await interaction.response.send_message("No se introducieron suficientes participantes.")
    else:
        random.shuffle(participantes)
        equipo1 = participantes[:len(participantes)//2]
        equipo2 = participantes[len(participantes)//2:]
        
        await interaction.response.send_message(f"Equipo 1:  {', '.join(equipo1)}\nEquipo 2:  {', '.join(equipo2)}")

@bot.tree.command(name="random_equipment", description="Te da un agente, una primaria y una pistola al azar de Valorant", guild=discord.Object(id=GUILD_ID))
async def random_equipment(interaction: discord.Interaction):
    agentes = ["Brimstone","Viper","Omen","Killjoy","Cypher","Sova","Sage","Phoenix","Jett","Reyna","Raze","Breach","Skye","Yoru","Astra","KAY/O","Chamber","Neon","Fade","Harbor","Gekko","Deadlock","Iso","Clove","Vyse","Tejo","Waylay"]
    primarias = ["Stinger","Spectre","Bucky","Judge","Bulldog","Guardian","Phantom","Vandal","Marshal","Operator","Outlaw","Ares","Odin"]
    pistolas = ["Classic","Shorty","Frenzy","Ghost","Sheriff"]
    
    r_agent = random.choice(agentes)
    r_primaria = random.choice(primarias)
    r_pistola = random.choice(pistolas)
    
    await interaction.response.send_message(f"{str(interaction.user.mention).capitalize()}, Esta partida la juegas con: \nAgente: {r_agent}\nPrimaria: {r_primaria}\nPistola: {r_pistola}")

@bot.tree.command(name="random_agent",description="Te da un Agente al azar del Valorant para que juegues una partida con él",guild=discord.Object(id=GUILD_ID))
async def random_agent(interaction: discord.Interaction):
    agentes = ["Brimstone","Viper","Omen","Killjoy","Cypher","Sova","Sage","Phoenix","Jett","Reyna","Raze","Breach","Skye","Yoru","Astra","KAY/O","Chamber","Neon","Fade","Harbor","Gekko","Deadlock","Iso","Clove","Vyse","Tejo","Waylay"]
    r_agent = random.choice(agentes)
    await interaction.response.send_message(f"{str(interaction.user).capitalize()}, Tu agente para esta partida es: {r_agent}")
    
@bot.tree.command(name="random_weapon",description="Te da un arma al azar para que juegues una partida solo jugando con ella (primario)",guild=discord.Object(id=GUILD_ID))
async def random_weapon(interaction: discord.Interaction):
    primarias = ["Stinger","Spectre","Bucky","Judge","Bulldog","Guardian","Phantom","Vandal","Marshal","Operator","Outlaw","Ares","Odin"]
    await interaction.response.send_message(f"{str(interaction.user).capitalize()}, Tu arma para esta partida es: {random.choice(primarias)}")
    
@bot.tree.command(name="random_pistol",description="Te da una pistola al azar para que la juegues en la siguiente partida",guild=discord.Object(id=GUILD_ID))
async def random_pistol(interaction: discord.Interaction):
    pistolas = ["Classic","Shorty","Frenzy","Ghost","Sheriff"]
    await interaction.response.send_message(f"{str(interaction.user).capitalize()}, Tu pistola para esta partida es: {random.choice(pistolas)}")

@bot.tree.command(name="desafiov", description="Desafios de Valorant, dificultad normal, facil, dificil, extremo o imposible", guild=discord.Object(id=GUILD_ID))
@app_commands.choices(dificultad= [
    app_commands.Choice(name="normal", value="normal"),
    app_commands.Choice(name="dificil", value="dificil"),
    app_commands.Choice(name="extremo", value="extremo"),
    app_commands.Choice(name="imposible", value="imposible"),
    app_commands.Choice(name="ridiculo", value="ridiculo")])
async def desafiov(interaction: discord.Interaction, dificultad: app_commands.Choice[str]):
    if dificultad.value == "normal":
        retosN = ["Desafio normal: Mata a 15 enemigos o más y se el que menos muera de tu equipo", "Haz mas de 10 asistencias","Mata a 7 enemigos a pistola", "Queda entre los 3 primeros", "No quedes en negativo","Termina cada call con nigger", "Solo puedes elegir agenes de color negro", "Entra siempre el ultimo al site","Si eres el unico con vida en tu equipo vs >1 enemigos, ve a por ellos a cuchillo"]
        await interaction.response.send_message("Desafio de dificultad Normal:\n"+random.choice(retosN))
    elif dificultad.value == "dificil":
        retosD = ["Desafio dificil: Mata a 20 enemigos o más y muere menos de 8 veces","No les puedes comprar a tus compañeros","No puedes usar pistolas que no sean la sheriff", "Juega con los cascos al reves", "No puedes saltar en toda la partida","Queda primero de la clasificación de tu equipo","Solo puedes usar el chat de voz GRITANDO", "Solo puedes usar el chat de voz susurrando" ]
        await interaction.response.send_message("Desafio de dificultad Dificil:\n"+random.choice(retosD))
    elif dificultad.value == "extremo":
        retosE = ["Mata a 25 enemigos o más y muere menos de 10 veces", "Juega solo con la Guardian y ve solo a headshot (tiros a la cabeza)", "Si compras un arma no la puedes volver a comprar hasta dentro de 4 rondas", "Mata 3 enemigos a cuchillo", "Juega sin hablarle a tu equipo de ninguna forma, ni texto ni voz (los pings son validos)", "Solo puedes comprar subfusiles como arma","Queda primero de la clasificación de la partida"]
        await interaction.response.send_message("Desafio de dificultad Extremo:\n"+random.choice(retosE))
    elif dificultad.value == "imposible":
        retosI= ["Mata a 30 enemigos o más y muere menos de 3 veces","Mata a 30 enemigos o más y no puedes usar habilidades", "Mata a 5 enemigos a cuchillo sin la ayuda de tus habilidades", "Juega la partida solo a pistolas y gana","Solo te puedes mover saltando en toda la partida","No puedes ragear, chillar o chillar susurrando, echarle la culpa a tus compañeros ni poner excusas, debes aceptar que eres un manco","Juega sin sonido del juego","Solo puedes moverte shifteando en toda la partida, no puedes ni andar ni correr al comenzar las rondas"]
        await interaction.response.send_message("Desafio de dificultad Imposible:\n"+random.choice(retosI))
    elif dificultad.value == "ridiculo":
        retosR = ["Si hay una mujer en tu equipo, debes de intertar ligartela","Si hay una mujer en tu equipo, no puedes hablar","Si alguien se hace un ace, debes de piropearle el resto de la partida durante todas las rondas","Si el enemigo se hace un ace, debes ir a por él a muerte","Ten más de 2 neuronas","Solo puedes hablar gimiendo","Por cada muerte, haz 1 flexión/abdominal","Juega mas de 3 partidas seguidas sin parar mas de 5 minutos entre partida y partida","Si alguien te dice algo sobre que deberias de hacer en la ronda, debes de trollear y hacer lo contrario"]
        await interaction.response.send_message("Desafio Ridiculo:\n"+random.choice(retosR))
    else: 
        await interaction.response.send_message("Dificultad no reconocida. Por favor, elige una de las opciones disponibles.")


@bot.command()
async def sorpresa(ctx,*args):
    try:
        await ctx.message.delete()
    except Exception:
        pass
    # Permite buscar por personaje y tags: !sorpresa personaje tag1 tag2 ...
    # Si el primer argumento es "personaje:nombre" o "character:nombre", lo usa como tag especial
    tags = []
    if len(args) >= 1:
        for arg in args:
            if arg.lower().startswith("personaje:"):
                # Convierte a formato de tag de rule34: character:nombre
                nombre = arg.split(":",1)[1].replace(' ', '_')
                tags.append(f"character:{nombre}")
            elif arg.lower().startswith("character:"):
                nombre = arg.split(":",1)[1].replace(' ', '_')
                tags.append(f"character:{nombre}")
            else:
                tags.append(str(arg).replace(' ', '_'))
    tags_str = " ".join(tags)
    url = f"https://api.rule34.xxx/index.php?page=dapi"+API_R+"&s=post&q=index&json=1"
    if tags_str:
        url += f"&tags={tags_str}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        datos = response.json()
    except Exception as e:
        print(f"[sorpresa] Error al buscar la imagen: {e}")
        return
    # Si es una lista de posts:
    if isinstance(datos, list) and len(datos) > 0:
        post = random.choice(datos)
        imagen_url = post.get("file_url")
        if imagen_url:
            await ctx.send(imagen_url, delete_after=5)
        else:
            print("[sorpresa] No se encontró imagen para esos tags/personaje.")
    else:
        print("[sorpresa] No se encontró nada para esos tags/personaje.")

@bot.command()
async def ruleta(ctx):
    author = ctx.author
    
    if author.voice and author.voice.channel:
        voice_channel = author.voice.channel
        members = voice_channel.members
        
        members_names = [member.mention for member in members]
        
        await ctx.send(f"El mas gay de este canal es: {random.choice(members_names)}")
        
    else:
        await ctx.send("No estas en un canal de voz")

@bot.command()
async def gato(ctx):
    ctx.message.delete()
    gato = random.choice(gatos)
    await ctx.send(file=discord.File(f"./gatos/{gato}"))

@bot.command()
async def pokemon(ctx,*args):
    try:
        pokemon = args[0].lower()
        result = requests.get("https://pokeapi.co/api/v2/pokemon/" + pokemon)
        if result.text == "Not Found":
            await ctx.send(f"Pokémon '{pokemon}' no encontrado.")
        else:
            imagen = result.json()['sprites']['front_default']
            await ctx.send(imagen)
    except Exception as e:
        print (f"An error occurred: {e}")

@pokemon.error
async def pokemon_error(ctx, error):
    if isinstance(error,commands.errors.MissingRequiredArgument):
        await ctx.send("Pasame el nombre del pkemon picha")

@bot.command()
async def chiste(ctx):
    await ctx.message.delete()
    response =requests.get("https://icanhazdadjoke.com/", headers={"Accept": "application/json"})

    if response.status_code == 200:
        datos = response.json()
        chiste = datos["joke"]
        await ctx.send(chiste)
    else:
        await ctx.send("Error al conectar con la API", ephemeral=True, delete_after=5)        
        
@bot.command()
async def join(ctx):
     if ctx.author.voice:
       if ctx.voice_client is None:
          channel = ctx.author.voice.channel
          await channel.connect()

          voice_client =  ctx.voice_client

          while voice_client.is_playing():
              await discord.utils.sleep_until(voice_client.is_playing())
        
@bot.command()
async def play(ctx):
    if not  ctx.voice_client:
        await join(ctx)
        ctx.voice_client.play(discord.FFmpegPCMAudio("./audios/fart.mp3"))

    else:
        ctx.voice_client.play(discord.FFmpegPCMAudio("./audios/fart.mp3"))
        

@bot.event
async def on_message(msg):  
    if msg.author.id == bot.user.id:
        return
    else:
        if msg.content.startswith("!"):
            try:
                await bot.process_commands(msg)
                return
            except commands.CommandNotFound:
                await msg.channel.send(f"Comando no encontrado: {msg.content}")
                return
        else:
            mensaje = msg.content.lower().replace(" ","")
            if mensaje == "¿quienesgay?" or mensaje == "quienesgay?" or mensaje == "quienesgay":
                await msg.channel.send(f"Valentin es el Gay mas grande de todos")
            else:
                return 
                #await msg.channel.send(f"{msg.author.mention} said: {msg.content}")


@bot.tree.command(name="greet", description="Sends a greeting to the user",guild=discord.Object(id=GUILD_ID))
async def greet(interaction: discord.Interaction):

    try:
        username = interaction.user.mention
        await interaction.response.send_message(f"Hello there, {username}")
    except Exception as e:
        print(f"An error occurred while creating the command: {e}")

bot.run(TOKEN)

