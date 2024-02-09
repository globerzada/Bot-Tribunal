import discord
from discord.ext import commands
from pymongo import MongoClient

client = MongoClient("oculto")
db = client["tribunaldados"]
collection = db["advertencias"]
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
users = []

#verifica se o bot foi logado
@bot.event
async def on_ready():
    print(f'{bot.user} está online')

#adiciona usuario a lista de réus
@bot.command('add')
async def add(ctx, member: discord.Member):
    if discord.utils.get(ctx.author.roles, name='ADM'):
        if not any(i['id'] == member.id for i in users):
            collection.insert_one({'userId':member.id, 'quantity':0, 'rolls':0, 'totQ': 0, 'pendingRolls': 0})
            print(users)
            await ctx.send(f'Parabéns você agora está na lista de réus do tribunal, {member.mention}. Todos os seus atos a partir de agora serão SEVERAMENTE julgados!')
        else:
            await ctx.send(f'{member.mention} já está sob julgamento CONSTANTE!')
    else:
        await ctx.send(f'{ctx.author.mention} não tem o cargo necessário para executar este comando!')

#adciona 1 advertencia ao usuario
@bot.command('adv')
async def add_adv(ctx, member: discord.Member, *, motivo = ''):
    if discord.utils.get(ctx.author.roles, name='ADM'):
        query = {"userId": member.id}
        person = collection.find_one(query) #verifica se o usuário está na lista de réus
        if person != None:
            person['quantity'] += 1
            person['totQ'] += 1
            totQ = person['totQ']
            person['motivo'] = motivo #adiciona o motivo ao dicionário
            reason = person['motivo']
            collection.update_one(query, {"$set": person})
            if person['quantity'] == 3:
                person['quantity'] = 0
                person['pendingRolls'] += 1
                collection.update_one(query, {"$set": person})
                await ctx.send(f'{ctx.author.mention} deu a terceira advertência de {member.mention}, que tem um total de {totQ} advertências. E o mesmo deverá ser PUNIDO passando pela ROLETA DA JUSTIÇA!!')
            else:
                await ctx.send(f'{ctx.author.mention} deu 1 advertência para {member.mention} com a justificativa: {reason}')
                print(person)
        else:
            await ctx.send(f'você ainda nâo está entre os réus {member.mention}, use o comando "/add @nomedeusuario"!')
    else:
        await ctx.send(f'{ctx.author.mention} não tem o cargo necessário para executar este comando!')

#remove 1 advertência do usuário marcado
@bot.command('radv')
async def remove_adv(ctx, member: discord.Member):
    if discord.utils.get(ctx.author.roles, name='ADM'):
        query = {"userId": member.id}
        person = collection.find_one(query) #verifica se o usuário está na lista de réus
        if person != None:
            if person['quantity'] > 0:
                person['quantity'] -= 1
                person['totQ'] -= 1
                collection.update_one(query, {'$set': person})
                await ctx.send(f'{ctx.author.mention} removeu a advertência de {member.mention}!')
            else:
                await ctx.send(f'{member.mention} não tem advertências para serem removidas')
        else:
            await ctx.send('Usuário não encontrado ou não cadastrado na lista de réus!')
    else:
        await ctx.send(f'{ctx.author.mention} não tem o cargo necessário para executar este comando!')

#Mostra quantas advertências o usuário que enviou a mensagem tem
@bot.command('qadv')
async def ver_adv(ctx):
    userid = ctx.author.id
    query = {"userId": userid}
    person = collection.find_one(query)
    if person != None:
        quantity = person['totQ']
        rolls = person['rolls']
        await ctx.send(f'{ctx.author.mention} tem {quantity} advertências e girou a roleta {rolls} vezes')
    else:
        await ctx.send('Usuário não encontrado ou não cadastrado na lista de réus!')

#lista com em ordem decrescente de advertências
@bot.command('toplist')
async def list_adv(ctx):
    mensagemInicial = 'LISTA DE ADVERTÊNCIAS:\n'
    mensagem = ''
    usersList = collection.find()
    sortedList = sorted(usersList, key=lambda x: x['totQ'], reverse=True)
    for i in sortedList:
        memberName = i['nomes']
        memberQtdAdv = i['totQ']
        memberQtdRolls = i['rolls']
        mensagem += (f'{memberName} - tem {memberQtdAdv} advertências e {memberQtdRolls} roletas!\n')
    await ctx.send(mensagemInicial+mensagem)

#lista em ordem decrescente das roletas pendentes
@bot.command('pendingrolls')
async def pending_rolls(ctx):
    mensagemInicial = 'ROLETAS PENDENTES:\n'
    mensagem = ''
    usersList = collection.find()
    sortedList = sorted(usersList, key=lambda x: x['totQ'], reverse=True)
    for i in sortedList:
        memberName = i['nomes']
        memberQtdPendingRolls = i['pendingRolls']
        mensagem += (f'{memberName} tem {memberQtdPendingRolls} roletas pendentes!\n')
    await ctx.send(mensagemInicial+mensagem)

#lista para confirmar que a roleta foi girada
@bot.command('confirmroll')
async def confirm_roll(ctx, member: discord.Member):
    if discord.utils.get(ctx.author.roles, name='ADM'):
        query = {"userId": member.id}
        person = collection.find_one(query)#verifica se o usuário está na lista de réus
        if person != None:
            if person['pendingRolls'] > 0:
                person['pendingRolls'] -= 1
                person['rolls'] += 1
                collection.update_one(query, {'$set': person})
                await ctx.send(f'{ctx.author.mention} confirmou que a roleta de {member.mention} foi realizada!')
            else:
                await ctx.send(f'{ctx.author.mention} O réu mencionado não tem roletas pendentes!')
        else:
            await ctx.send('Usuário não encontrado ou não cadastrado na lista de réus!')
    else:
        await ctx.send(f'{ctx.author.mention} não tem o cargo necessário para executar este comando!')

#fala o motivo da última advertência
@bot.command('madv')
async def adv_reason(ctx):
    userid = ctx.author.id
    query = {"userId": userid}
    person = collection.find_one(query)
    if person != None:
        reason = person['motivo']
        await ctx.send(f'{ctx.author.mention} o motivo de sua última advertência foi: {reason}')
    else:
        ctx.send('o usuário não está cadastrado na lista de réus')

#mostra a lista de comandos
bot.remove_command('help')
@bot.command('helpt')
async def help(ctx):
    await ctx.send("""             Os comandos do Tribunal são:
        COMANDOS DE ADMIN:
                       
  -"/adduser @nomedousuario" para adicionar o usuário a lista de réus.
  -"/adv @nomedousuario motivo da advertencia" adiciona 1 advertência do réu que foi mencionado.
  -"/confirmroll @nomedousuario" confirma que rodou a roleta do réu mencionado.
  -"/radv @nomedousuario" remove 1 advertência do réu que foi mencionado.
  -"/pendingrolls" mostra uma tabela com as roletas pendentes.
                                              
          COMANDOS GERAIS:
                       
  -"/help" para mostrar os comandos do bot.
  -"/madv" mostra o motivo de sua última advertência.
  -"/pendingrolls" mostra uma tabela com as roletas pendentes
  -"/topadv" mostra uma lista com todos os réus do Tribunal.""")

bot.run("oculto")