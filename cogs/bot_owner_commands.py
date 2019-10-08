import logging
import discord
from discord.ext import commands
from helpers.embed_handler import success_embed, failure_embed
from helpers.misc import tail
from helpers.paginator import Paginator
from helpers.converters import license_duration
from helpers.licence_helper import construct_expiration_date

logger = logging.getLogger(__name__)


class BotOwnerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def update(self, ctx, *, msg=None):
        if msg is None:
            msg = """Update in progress.
                    Non breaking changes that will not affect bot usage/performance."""
        await self.bot.change_presence(activity=discord.Game(name=msg))
        await ctx.send(success_embed("Successfully changed status.", ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def playing(self, ctx, *, game):
        await self.bot.change_presence(activity=discord.Game(name=game))
        logger.info(f"Successfully set presence to **Playing {game}**.")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def streaming(self, ctx, name, url):
        """
        Discord py currently only supports twitch urls.

        """
        if "//www.twitch.tv" not in url:
            await ctx.send(embed=failure_embed("Only twitch urls supported!"))
            return
        await self.bot.change_presence(activity=discord.Streaming(name=name, url=url))
        logger.info(f"Successfully set presence to **Streaming {name}**.")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def listening(self, ctx, *, song):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=song))
        logger.info(f"Successfully set presence to **Listening to {song}**.")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def watching(self, ctx, *, movie):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=movie))
        logger.info(f"Successfully set presence to **Watching {movie}**.")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload_config(self, ctx):
        """
        Reloads json config.

        """
        self.bot.config.reload_config()
        msg = "Successfully reloaded config."
        logger.info(msg)
        await ctx.send(embed=success_embed(msg, ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def show_log(self, ctx, lines=100):
        """
        Shows last n lines from log.txt

        Max lines 10 000.
        Sends multiple messages at once if needed.
        """
        if lines > 10_000:
            lines = 10_000

        log = "".join(tail(lines))
        await Paginator.paginate(self.bot, ctx.author, ctx.author, log,
                                 title=f"Last {lines} log lines.\n\n", prefix="```DNS\n")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def valid(self, ctx, license):
        """
        Checks if passed license is valid

        """
        if await self.bot.main_db.is_valid_license(license, ctx.guild.id):
            await ctx.send(embed=success_embed("License is valid", ctx.me))
        else:
            await ctx.send(embed=failure_embed(f"License is not valid."))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def guilds_diagnostic(self, ctx):
        loaded_guilds = tuple(guild.id for guild in self.bot.guilds)
        db_guilds = await self.bot.main_db.get_all_guild_ids()
        difference = set(loaded_guilds).symmetric_difference(set(db_guilds))
        difference = None if len(difference) == 0 else difference
        message = (f"Loaded guilds: {len(loaded_guilds)}\n"
                   f"Database guilds: {len(db_guilds)}\n"
                   f"Difference: {difference}")
        await ctx.send(embed=success_embed(message, ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def force_remove_all_guild_data(self, ctx, guild_too: int = 0):
        """
        :param guild_too: default 0. Pass 1 to delete guild table too.

        """
        await self.bot.main_db.remove_all_guild_data(ctx.guild.id, guild_too)
        await ctx.send(embed=success_embed("Done", ctx.me))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def force_new_licensed_member(self, ctx, member: discord.Member, role: discord.Role,
                                        *, license_dur: license_duration):
        expiration_date = construct_expiration_date(license_dur)
        await self.bot.main_db.add_new_licensed_member(member.id, ctx.guild.id, expiration_date, role.id)
        await ctx.send(embed=success_embed("Done", ctx.me))


def setup(bot):
    bot.add_cog(BotOwnerCommands(bot))
