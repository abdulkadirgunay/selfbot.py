'''
MIT License

Copyright (c) 2017 Grok

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import discord
from discord.ext import commands
from urllib.parse import urlparse
from ext import embedtobox
import datetime
import asyncio
import psutil
import random
import pip
import json
import os
import io


class Information:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(no_pm=True)
    async def channels(self, ctx, serverid:int = None):
        """Tüm kanalları gösterir, akıllıca kullanın!"""

        if serverid is None:
            server = ctx.guild
        else:
            server = discord.utils.get(self.bot.guilds, id=serverid)
            if server is None:
                return await ctx.send('Sunucu bulunamadı!')

        e = discord.Embed()
        e.color = await ctx.get_dominant_color()

        voice = ''
        text = ''
        categories = ''

        for channel in server.voice_channels:
            voice += f'\U0001f508 {channel}\n'
        for channel in server.categories:
            categories += f'\U0001f4da {channel}\n'
        for channel in server.text_channels:
            text += f'\U0001f4dd {channel}\n'
        
        if len(server.text_channels) > 0:
            e.add_field(name='Metin Kanalları', value=f'```{text}```')
        if len(server.categories) > 0:
            e.add_field(name='Kategoriler', value=f'```{categories}```')
        if len(server.voice_channels) > 0:
            e.add_field(name='Ses Kanalları', value=f'```{voice}```')

        try:
            await ctx.send(embed=e)
        except discord.HTTPException:
            em_list = await embedtobox.etb(e)
            for page in em_list:
                await ctx.send(page)

    @commands.command(aliases=["ri","role"], no_pm=True)
    @commands.guild_only()
    async def roleinfo(self, ctx, *, role: discord.Role):
        '''Rol hakkındaki bilgileri gösterir.'''
        guild = ctx.guild

        since_created = (ctx.message.created_at - role.created_at).days
        role_created = role.created_at.strftime("%d %b %Y %H:%M")
        created_on = "{} ({} days ago!)".format(role_created, since_created)
        members = ''
        i = 0
        for user in role.members:
            members += f'{user.name}, '
            i+=1
            if i > 30:
                break

        if str(role.colour) == "#000000":
            colour = "default"
            color = ("#%06x" % random.randint(0, 0xFFFFFF))
            color = int(colour[1:], 16)
        else:
            colour = str(role.colour).upper()
            color = role.colour

        em = discord.Embed(colour=color)
        em.set_author(name=role.name)
        em.add_field(name="Kullanıcılar", value=len(role.members))
        em.add_field(name="Etiketlenmiş", value=role.mentionable)
        em.add_field(name="Vinç", value=role.hoist)
        em.add_field(name="Pozisyon", value=role.position)
        em.add_field(name="Yönetilen", value=role.managed)
        em.add_field(name="Renk", value=colour)
        em.add_field(name='Oluşturulma Tarihi', value=created_on)
        em.add_field(name='Üyeler', value=members[:-2], inline=False)
        em.set_footer(text=f'Rol ID: {role.id}')

        await ctx.send(embed=em)

    @commands.command(aliases=['av'])
    async def avatar(self, ctx, *, member : discord.Member=None):
        '''Birinin avatar URL sini döndürür'''
        member = member or ctx.author
        av = member.avatar_url
        if ".gif" in av:
            av += "&f=.gif"
        color = await ctx.get_dominant_color(av)
        em = discord.Embed(url=av, color=color)
        em.set_author(name=str(member), icon_url=av)
        em.set_image(url=av)
        try:
            await ctx.send(embed=em)
        except discord.HTTPException:
            em_list = await embedtobox.etb(em)
            for page in em_list:
                await ctx.send(page)
            try:
                async with ctx.session.get(av) as resp:
                    image = await resp.read()
                with io.BytesIO(image) as file:
                    await ctx.send(file=discord.File(file, 'avatar.png'))
            except discord.HTTPException:
                await ctx.send(av)

    @commands.command(aliases=['servericon'], no_pm=True)
    async def serverlogo(self, ctx):
        '''Sunucunun simge URL sini döndürür.'''
        icon = ctx.guild.icon_url
        color = await ctx.get_dominant_color(icon)
        server = ctx.guild
        em = discord.Embed(color=color, url=icon)
        em.set_author(name=server.name, icon_url=icon)
        em.set_image(url=icon)
        try:
            await ctx.send(embed=em)
        except discord.HTTPException:
            em_list = await embedtobox.etb(em)
            for page in em_list:
                await ctx.send(page)
            try:
                async with ctx.session.get(icon) as resp:
                    image = await resp.read()
                with io.BytesIO(image) as file:
                    await ctx.send(file=discord.File(file, 'serverlogo.png'))
            except discord.HTTPException:
                await ctx.send(icon)

    @commands.command(aliases=['server','si','svi'], no_pm=True)
    @commands.guild_only()
    async def serverinfo(self, ctx, server_id : int=None):
        '''Sunucu hakkındaki bilgileri görün.'''
        server = self.bot.get_server(id=server_id) or ctx.guild
        total_users = len(server.members)
        online = len([m for m in server.members if m.status != discord.Status.offline])
        text_channels = len([x for x in server.channels if isinstance(x, discord.TextChannel)])
        voice_channels = len([x for x in server.channels if isinstance(x, discord.VoiceChannel)])
        categories = len(server.channels) - text_channels - voice_channels
        passed = (ctx.message.created_at - server.created_at).days
        created_at = "Since {}. That's over {} days ago!".format(server.created_at.strftime("%d %b %Y %H:%M"), passed)

        colour = await ctx.get_dominant_color(server.icon_url)

        data = discord.Embed(description=created_at,colour=colour)
        data.add_field(name="Bölge", value=str(server.region))
        data.add_field(name="Kullanıcılar", value="{}/{}".format(online, total_users))
        data.add_field(name="Metin Kanalları", value=text_channels)
        data.add_field(name="Ses Kanalları", value=voice_channels)
        data.add_field(name="Kategoriler", value=categories)
        data.add_field(name="Roller", value=len(server.roles))
        data.add_field(name="Sahip", value=str(server.owner))
        data.set_footer(text="Sunucu ID: " + str(server.id))
        data.set_author(name=server.name, icon_url=None or server.icon_url)
        data.set_thumbnail(url=None or server.icon_url)
        try:
            await ctx.send(embed=data)
        except discord.HTTPException:
            em_list = await embedtobox.etb(data)
            for page in em_list:
                await ctx.send(page)

    @commands.command()
    async def tags(self, ctx, *, text: str=None):
        ''' Yararlı selfbot Etiketleri ve öğreticiler alın '''
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        with open('data/tags.json', 'r') as f:
            s = f.read()
            tags = json.loads(s)
        if text in tags:
            await ctx.send(f'{tags[str(text)]}')
        else:
            p = f' {ctx.prefix}{ctx.invoked_with} '
            usage = f'\n***AVAILABLE TAGS:***\n\n' \
                    f'`1.`{p}heroku\n`2.`{p}change-token\n' \
                    f'`3.`{p}hosting\n`4.`{p}rules-selfbot\n`5.`{p}tutorial\n' \
                    f'`6.`{p}update\n`7.`{p}support-invite\n`8.`{p}support\n' \
                    f'`9.`{p}android-token\n`10.`{p}android-heroku'
            e = discord.Embed()
            e.color = await ctx.get_dominant_color(url=ctx.message.author.avatar_url)
            e.add_field(name='Etiket bulunamadı!', value=usage)
            try:
                await ctx.send(embed=e, delete_after=15)
            except Exception as e:
                await ctx.send(f'```{e}```')

    @commands.command(aliases=['ui'], no_pm=True)
    @commands.guild_only()
    async def userinfo(self, ctx, *, member : discord.Member=None):
        '''Sunucu üyesi hakkında bilgi edin!'''
        server = ctx.guild
        user = member or ctx.message.author
        avi = user.avatar_url
        roles = sorted(user.roles, key=lambda c: c.position)

        for role in roles:
            if str(role.color) != "#000000":
                color = role.color
        if 'color' not in locals():
            color = 0

        rolenames = ', '.join([r.name for r in roles if r.name != "@everyone"]) or 'None'
        time = ctx.message.created_at
        desc = '{0} is chilling in {1} mode.'.format(user.name, user.status)
        member_number = sorted(server.members, key=lambda m: m.joined_at).index(user) + 1

        em = discord.Embed(colour=color, description=desc, timestamp=time)
        em.add_field(name='Nick', value=user.nick, inline=True)
        em.add_field(name='Üye No.',value=str(member_number),inline = True)
        em.add_field(name='Hesap Oluşturuldu', value=user.created_at.__format__('%A, %d. %B %Y'))
        em.add_field(name='Giriş Tarihi', value=user.joined_at.__format__('%A, %d. %B %Y'))
        em.add_field(name='Rolleri', value=rolenames, inline=True)
        em.set_footer(text='Kullanıcı ID: '+str(user.id))
        em.set_thumbnail(url=avi)
        em.set_author(name=user, icon_url=server.icon_url)

        try:
            await ctx.send(embed=em)
        except discord.HTTPException:
            em_list = await embedtobox.etb(em)
            for page in em_list:
                await ctx.send(page)

    @commands.command(aliases=['bot', 'info'])
    async def about(self, ctx):
        '''Bot ve son değişiklikler hakkındaki bilgileri görün.'''

        embed = discord.Embed()
        embed.url = 'https://discord.gg/PxUbnYv'
        embed.colour = await ctx.get_dominant_color(ctx.author.avatar_url)

        embed.set_author(name='dtpk.py', icon_url=ctx.author.avatar_url)

        total_members = sum(1 for _ in self.bot.get_all_members())
        total_online = len({m.id for m in self.bot.get_all_members() if m.status is discord.Status.online})
        total_unique = len(self.bot.users)

        voice_channels = []
        text_channels = []
        for guild in self.bot.guilds:
            voice_channels.extend(guild.voice_channels)
            text_channels.extend(guild.text_channels)

        text = len(text_channels)
        voice = len(voice_channels)
        dm = len(self.bot.private_channels)

        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        fmt = '{h}h {m}m {s}s'
        if days:
            fmt = '{d}d ' + fmt
        uptime = fmt.format(d=days, h=hours, m=minutes, s=seconds)


        server = '[TIKLA](https://discord.gg/PxUbnYv)'


        embed.add_field(name='Yazar', value='kyb3r#7220')
	embed.add_field(name='Sahip', value='Abdülkadir GÜNAY#6582')
        embed.add_field(name='Çalışma Süresi', value=uptime)
        embed.add_field(name='Sunucular', value=len(self.bot.guilds))
        embed.add_field(name='Kullanıcılar', value=f'{total_unique} total\n{total_online} online')
        embed.add_field(name='Kanallar', value=f'{text} text\n{voice} voice\n{dm} direct')
        memory_usage = self.bot.process.memory_full_info().uss / 1024**2
        cpu_usage = self.bot.process.cpu_percent() / psutil.cpu_count()
        embed.add_field(name='Süreç', value=f'{memory_usage:.2f} MiB\n{cpu_usage:.2f}% CPU')
        embed.add_field(name='Discord', value=server)
        embed.set_footer(text=f'discord.py tarafından desteklenmektedir. {discord.__version__}')
        await ctx.send(embed=embed)


def setup(bot):
	bot.add_cog(Information(bot))
