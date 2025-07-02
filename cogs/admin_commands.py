"""
Admin Commands Cog for Lamy.
Implements developer-only slash commands for system management.
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional
import os
from datetime import datetime

from core.orchestration import OrchestrationCore
from core.models import MemorySearchQuery

logger = logging.getLogger(__name__)


class AdminCommands(commands.Cog):
    """
    Admin commands for managing Lamy's systems.
    All commands are restricted to the developer only.
    """
    
    def __init__(self, bot: commands.Bot, orchestrator: OrchestrationCore):
        """
        Initialize the admin commands.
        
        Args:
            bot: The Discord bot instance
            orchestrator: The orchestration core for system management
        """
        self.bot = bot
        self.orchestrator = orchestrator
        self.developer_id = int(os.getenv("DEVELOPER_ID", "0"))
        
    def is_developer(self, interaction: discord.Interaction) -> bool:
        """Check if the user is the developer."""
        return interaction.user.id == self.developer_id
        
    @app_commands.command(name="status", description="봇의 운영 상태를 확인합니다")
    async def status(self, interaction: discord.Interaction):
        """
        Show bot operational status and memory statistics.
        Developer only command.
        """
        if not self.is_developer(interaction):
            await interaction.response.send_message(
                "개발자만 쓸 수 있는 명령어야. 다른 거나 해.", 
                ephemeral=True
            )
            return
            
        # Get memory stats
        stats = self.orchestrator.get_memory_stats()
        
        # Create status embed
        embed = discord.Embed(
            title="라미 시스템 상태",
            color=discord.Color.dark_grey(),
            timestamp=datetime.utcnow()
        )
        
        # Bot info
        embed.add_field(
            name="봇 정보",
            value=f"**이름:** {self.bot.user.name}\n"
                  f"**ID:** {self.bot.user.id}\n"
                  f"**서버 수:** {len(self.bot.guilds)}\n"
                  f"**지연 시간:** {round(self.bot.latency * 1000)}ms",
            inline=True
        )
        
        # Memory stats
        embed.add_field(
            name="메모리 시스템",
            value=f"**작업 기억 채널:** {stats['working_memory_channels']}\n"
                  f"**작업 기억 메시지:** {stats['working_memory_total_messages']}\n"
                  f"**일화 기억:** {'활성화' if stats['episodic_memory_enabled'] else '비활성화'}",
            inline=True
        )
        
        # Core identity
        identity = stats['core_identity']
        embed.add_field(
            name="핵심 정체성",
            value=f"**이름:** {identity['name']}\n"
                  f"**성격:** {identity['personality']}\n"
                  f"**창조자:** {identity['creator']}",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @app_commands.command(name="memory-view", description="최근 일화 기억을 확인합니다")
    @app_commands.describe(user="특정 사용자의 기억만 필터링 (선택사항)")
    async def memory_view(
        self, 
        interaction: discord.Interaction,
        user: Optional[discord.Member] = None
    ):
        """
        View recent episodic memories, optionally filtered by user.
        Developer only command.
        """
        if not self.is_developer(interaction):
            await interaction.response.send_message(
                "개발자만 쓸 수 있는 명령어야. 다른 거나 해.", 
                ephemeral=True
            )
            return
            
        await interaction.response.defer(ephemeral=True)
        
        # Search for memories
        query = MemorySearchQuery(
            user_id=str(user.id) if user else None,
            limit=10
        )
        
        memories = await self.orchestrator.memory_manager.search_episodic_memory(query)
        
        if not memories:
            await interaction.followup.send(
                "저장된 기억이 없네. 뭐, 기억할 만한 게 있었나 싶기도 하고.", 
                ephemeral=True
            )
            return
            
        # Create embed for memories
        embed = discord.Embed(
            title=f"최근 일화 기억",
            description=f"{'전체' if not user else f'{user.name}님의'} 기억... 뭐, 기억할 만한 게 있었나.",
            color=discord.Color.dark_blue(),
            timestamp=datetime.utcnow()
        )
        
        for i, memory in enumerate(memories[:5], 1):
            embed.add_field(
                name=f"{i}. {memory.user_name} ({memory.timestamp.strftime('%Y-%m-%d %H:%M')})",
                value=f"**사용자:** {memory.user_message[:50]}{'...' if len(memory.user_message) > 50 else ''}\n"
                      f"**라미:** {memory.bot_response[:50]}{'...' if len(memory.bot_response) > 50 else ''}\n"
                      f"**관련성:** {memory.relevance_score:.2f}",
                inline=False
            )
            
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    @app_commands.command(name="memory-wipe-thread", description="현재 채널의 작업 기억을 초기화합니다")
    async def memory_wipe_thread(self, interaction: discord.Interaction):
        """
        Clear working memory for the current channel.
        Developer only command.
        """
        if not self.is_developer(interaction):
            await interaction.response.send_message(
                "개발자만 쓸 수 있는 명령어야. 다른 거나 해.", 
                ephemeral=True
            )
            return
            
        channel_id = str(interaction.channel_id)
        self.orchestrator.clear_working_memory(channel_id)
        
        await interaction.response.send_message(
            f"작업 기억을 지웠어. 이제 새로운 대화를 시작할 수 있겠네... 또 같은 얘기 반복하겠지만.",
            ephemeral=True
        )
        
    @app_commands.command(name="force-consolidation", description="기억 통합을 수동으로 실행합니다")
    async def force_consolidation(self, interaction: discord.Interaction):
        """
        Manually trigger memory consolidation for the current channel.
        Developer only command.
        """
        if not self.is_developer(interaction):
            await interaction.response.send_message(
                "개발자만 쓸 수 있는 명령어야. 다른 거나 해.", 
                ephemeral=True
            )
            return
            
        await interaction.response.defer(ephemeral=True)
        
        channel_id = str(interaction.channel_id)
        result = await self.orchestrator.force_consolidation(channel_id)
        
        embed = discord.Embed(
            title="기억 통합 완료",
            color=discord.Color.dark_green(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="처리 결과",
            value=f"**처리된 메시지:** {result['processed_messages']}\n"
                  f"**생성된 일화 기억:** {result['episodic_memories_created']}\n"
                  f"**추출된 의미 사실:** {result['semantic_facts_extracted']}\n"
                  f"**처리 시간:** {result['processing_time']:.2f}초",
            inline=False
        )
        
        if result['errors']:
            embed.add_field(
                name="오류",
                value="\n".join(result['errors'][:3]),
                inline=False
            )
            
        embed.add_field(
            name="요약",
            value=result['summary'],
            inline=False
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    @app_commands.command(name="reload-persona", description="페르소나 파일을 다시 로드합니다")
    async def reload_persona(self, interaction: discord.Interaction):
        """
        Reload persona file without restarting the bot.
        Developer only command.
        """
        if not self.is_developer(interaction):
            await interaction.response.send_message(
                "개발자만 쓸 수 있는 명령어야. 다른 거나 해.", 
                ephemeral=True
            )
            return
            
        try:
            # Reload persona
            self.orchestrator.llm_interface.reload_persona()
            
            await interaction.response.send_message(
                "페르소나 파일을 다시 로드했어. 이제 바뀐 성격으로 대화할 거야... 뭐, 크게 달라질 건 없겠지만.",
                ephemeral=True
            )
            logger.info("Persona reloaded via slash command")
            
        except Exception as e:
            logger.error(f"Error reloading persona: {str(e)}")
            await interaction.response.send_message(
                f"페르소나 로드 중 에러가 발생했어: {str(e)}",
                ephemeral=True
            )
            
    @app_commands.command(name="get-last-prompt", description="마지막 LLM 프롬프트를 확인합니다")
    @app_commands.describe(user="특정 사용자의 마지막 메시지에 대한 프롬프트 (선택사항)")
    async def get_last_prompt(
        self, 
        interaction: discord.Interaction,
        user: Optional[discord.Member] = None
    ):
        """
        Get the last prompt sent to the LLM for debugging.
        Developer only command.
        """
        if not self.is_developer(interaction):
            await interaction.response.send_message(
                "개발자만 쓸 수 있는 명령어야. 다른 거나 해.", 
                ephemeral=True
            )
            return
            
        last_prompt = self.orchestrator.get_last_prompt()
        
        if not last_prompt:
            await interaction.response.send_message(
                "아직 생성된 프롬프트가 없어. 뭐, 없으면 없는 거지.",
                ephemeral=True
            )
            return
            
        # Send as a file if too long
        if len(last_prompt) > 1900:
            # Create a text file with the prompt
            import io
            file = discord.File(
                io.StringIO(last_prompt),
                filename=f"last_prompt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            await interaction.response.send_message(
                "마지막 프롬프트가 너무 길어서 파일로 보내줄게. 귀찮지만 뭐...",
                file=file,
                ephemeral=True
            )
        else:
            # Send in code block
            await interaction.response.send_message(
                f"**마지막 LLM 프롬프트:**\n```\n{last_prompt}\n```",
                ephemeral=True
            )
            
    async def cog_app_command_error(
        self, 
        interaction: discord.Interaction, 
        error: app_commands.AppCommandError
    ):
        """Handle errors in slash commands."""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"좀 기다려. {error.retry_after:.1f}초 후에 다시 해.",
                ephemeral=True
            )
        else:
            logger.error(f"Error in command {interaction.command}: {str(error)}")
            await interaction.response.send_message(
                "또 에러야. 놀랍지도 않네.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """
    Setup function for the cog.
    
    Args:
        bot: The Discord bot instance
    """
    orchestrator = getattr(bot, 'orchestrator', None)
    if not orchestrator:
        raise ValueError("Bot must have an orchestrator attribute")
        
    await bot.add_cog(AdminCommands(bot, orchestrator)) 