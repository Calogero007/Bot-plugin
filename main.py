import os
import subprocess
import zipfile
import shutil
import discord
from discord.ext import commands

TOKEN = "MTUyNDg0MTU1NTMzOTUwOTg3MA.GT1QHc.emdny372sXm6YLuHuIOvCMmDo-OJ7uSmfDeYEI"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SMALL_CAPS_MAP = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ', 
    'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 
    'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ', 
    'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ'
}

def to_small_caps(text: str) -> str:
    return "".join(SMALL_CAPS_MAP.get(char.lower(), char) for char in text)

@bot.command(name="compila")
async def compila(ctx):
    """Estrae un file .zip allegato ed esegue build.sh"""
    
    # Controlla se l'utente ha allegato un file
    if not ctx.message.attachments:
        await ctx.reply(to_small_caps("errore: allega il file .zip del tuo progetto!"))
        return

    allegato = ctx.message.attachments[0]
    if not allegato.filename.endswith('.zip'):
        await ctx.reply(to_small_caps("errore: il file deve essere in formato .zip!"))
        return

    await ctx.reply(to_small_caps("ricevuto! estrazione e compilazione in corso..."))

    # Cartelle temporanee per non fare confusione sul server
    base_dir = os.path.dirname(os.path.abspath(__file__))
    work_dir = os.path.join(base_dir, f"build_{ctx.author.id}")
    zip_path = os.path.join(base_dir, allegato.filename)

    # 1. Scarica il file zip dall'utente
    await allegato.save(zip_path)

    # 2. Estrai il file zip nella cartella di lavoro
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(work_dir)

    # Cerca il file build.sh nella cartella estratta
    build_script_path = os.path.join(work_dir, "build.sh")

    if not os.path.exists(build_script_path):
        await ctx.reply(to_small_caps("errore: non ho trovato il file build.sh nel tuo .zip!"))
        # Pulizia
        os.remove(zip_path)
        shutil.rmtree(work_dir)
        return

    try:
        # 3. Dai i permessi di esecuzione a build.sh (necessario su Linux)
        os.chmod(build_script_path, 0o755)

        # 4. Esegui build.sh
        process = subprocess.run(
            ["./build.sh"], 
            cwd=work_dir, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            timeout=120
        )

        if process.returncode != 0:
            error_log = (process.stderr if process.stderr else process.stdout)[:1500]
            await ctx.reply(f"{to_small_caps('errore durante build.sh:')}\n```\n{error_log}\n```")
            return

        # 5. Cerca il file .jar generato (ovunque si trovi nella cartella di lavoro)
        jar_file_path = None
        for root, dirs, files in os.walk(work_dir):
            for file in files:
                if file.endswith(".jar") and "original-" not in file:
                    jar_file_path = os.path.join(root, file)
                    break
            if jar_file_path:
                break

        if jar_file_path:
            # Invia il file .jar all'utente
            discord_file = discord.File(jar_file_path)
            await ctx.reply(content=to_small_caps("compilazione riuscita! ecco il tuo plugin:"), file=discord_file)
        else:
            await ctx.reply(to_small_caps("errore: il tuo build.sh è terminato ma non ha generato nessun file .jar."))

    except subprocess.TimeoutExpired:
        await ctx.reply(to_small_caps("errore: lo script ha richiesto troppo tempo ed è stato interrotta."))
    finally:
        # Pulizia finale dei file temporanei per non riempire l'hosting
        if os.path.exists(zip_path):
            os.remove(zip_path)
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)

bot.run(TOKEN)
