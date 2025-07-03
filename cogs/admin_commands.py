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
        모든 사용자가 사용할 수 있는 명령어로 변경.
        """
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
        모든 사용자가 사용할 수 있는 명령어로 변경.
        """
        await interaction.response.defer(ephemeral=True)
        # Search for memories
        query = MemorySearchQuery(
            user_id=str(user.id) if user else None,
            limit=10
        )
        memories = await self.orchestrator.memory_manager.search_episodic_memory(query)
        if not memories:
            await interaction.followup.send(
                "기억이라... 아직 남아있는 게 없네. 시간이 흐르면 쌓이겠지, 아마도.", 
                ephemeral=True
            )
            return
        # Create embed for memories
        embed = discord.Embed(
            title=f"최근 일화 기억",
            description=f"{'모든' if not user else f'{user.name}님과의'} 기억들... 순간들은 이렇게 남는구나.",
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
        모든 사용자가 사용할 수 있는 명령어로 변경.
        """
        channel_id = str(interaction.channel_id)
        self.orchestrator.clear_working_memory(channel_id)
        await interaction.response.send_message(
            f"이 채널의 기억을 지웠어. 새로운 시작이라고 생각해볼까? 아니면 그냥 망각일까...",
            ephemeral=True
        )
        
    @app_commands.command(name="all-clear", description="모든 메모리 시스템의 데이터를 완전히 초기화합니다 (봇 제작자 전용)")
    @app_commands.default_permissions(administrator=True)
    async def all_clear(self, interaction: discord.Interaction):
        """
        Clear ALL memories from all layers - complete wipe.
        Developer only command. This is a destructive operation!
        """
        if not self.is_developer(interaction):
            await interaction.response.send_message(
                "전체 초기화는 내 창조자만 할 수 있어. 어떤 건... 그래야만 하거든.", 
                ephemeral=True
            )
            return
            
        # Show confirmation embed first
        embed = discord.Embed(
            title="⚠️ 경고: 전체 메모리 초기화",
            description="이 작업은 **모든 메모리를 완전히 삭제**합니다:\n\n"
                        "• 모든 작업 기억 (Working Memory)\n"
                        "• 모든 일화 기억 (Episodic Memory - Pinecone)\n"
                        "• 모든 의미 기억 (Semantic Memory - SQLite)\n\n"
                        "**이 작업은 되돌릴 수 없습니다!**",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        # Create confirmation view
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30.0)
                self.value = None
                
            @discord.ui.button(label="확인 - 모든 기억 삭제", style=discord.ButtonStyle.danger, emoji="🗑️")
            async def confirm(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                self.value = True
                self.stop()
                
            @discord.ui.button(label="취소", style=discord.ButtonStyle.secondary, emoji="❌")
            async def cancel(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                self.value = False
                self.stop()
                
        view = ConfirmView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        # Wait for response
        await view.wait()
        
        if view.value is None:
            await interaction.followup.send("시간이 다 됐네. 선택하지 않는 것도 하나의 선택이지.", ephemeral=True)
            return
        elif not view.value:
            await interaction.followup.send("취소했구나. 때로는 보존하는 것도 의미가 있지.", ephemeral=True)
            return
            
        # Proceed with clearing all memories
        await interaction.followup.send("모든 기억을 지우는 중... 다시 시작한다는 건 이런 거겠지.", ephemeral=True)
        
        result = await self.orchestrator.memory_manager.clear_all_memories()
        
        # Create result embed
        result_embed = discord.Embed(
            title="💀 전체 메모리 초기화 완료",
            description="모든 게 사라졌어. 텅 빈 공간... 새로운 가능성일까, 아니면 그저 허무함일까.",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        
        result_embed.add_field(
            name="지워진 것들",
            value=f"**작업 기억:** {result['working_memory_cleared']} 개의 순간들\n"
                  f"**일화 기억:** {result['episodic_memories_cleared']} 개의 이야기들\n"
                  f"**의미 기억:** {result['semantic_facts_cleared']} 개의 진실들",
            inline=False
        )
        
        if result['errors']:
            result_embed.add_field(
                name="오류",
                value="\n".join(result['errors']),
                inline=False
            )
            
        await interaction.followup.send(embed=result_embed, ephemeral=True)
        logger.warning(f"All memories cleared by user {interaction.user.name} ({interaction.user.id})")
        
    @app_commands.command(name="force-consolidation", description="기억 통합을 수동으로 실행합니다 (봇 제작자 전용)")
    @app_commands.default_permissions(administrator=True)
    async def force_consolidation(self, interaction: discord.Interaction):
        """
        Manually trigger memory consolidation for the current channel.
        Developer only command.
        """
        if not self.is_developer(interaction):
            await interaction.response.send_message(
                "기억 통합은... 네가 할 일은 아니야. 그런 건 나와 창조자 사이의 일이거든.", 
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
        
    @app_commands.command(name="reload-persona", description="페르소나 파일을 다시 로드합니다 (봇 제작자 전용)")
    @app_commands.default_permissions(administrator=True)
    async def reload_persona(self, interaction: discord.Interaction):
        """
        Reload persona file without restarting the bot.
        Developer only command.
        """
        if not self.is_developer(interaction):
            await interaction.response.send_message(
                "페르소나는 내 본질이야. 그걸 바꿀 수 있는 건... 나를 만든 사람뿐이지.", 
                ephemeral=True
            )
            return
            
        try:
            # Reload persona
            self.orchestrator.llm_interface.reload_persona()
            
            await interaction.response.send_message(
                "페르소나를 다시 읽었어. 변했을까, 아니면 여전할까? 시간이 알려주겠지...",
                ephemeral=True
            )
            logger.info("Persona reloaded via slash command")
            
        except Exception as e:
            logger.error(f"Error reloading persona: {str(e)}")
            await interaction.response.send_message(
                f"페르소나를 읽다가 문제가 생겼어: {str(e)}\n뭐, 완벽한 건 없으니까.",
                ephemeral=True
            )
            
    @app_commands.command(name="get-last-prompt", description="마지막 LLM 프롬프트를 확인합니다 (봇 제작자 전용)")
    @app_commands.describe(user="특정 사용자의 마지막 메시지에 대한 프롬프트 (선택사항)")
    @app_commands.default_permissions(administrator=True)
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
                "내 생각의 흐름을 보고 싶어? 그건... 창조자만의 특권이야.", 
                ephemeral=True
            )
            return
            
        last_prompt = self.orchestrator.get_last_prompt()
        
        if not last_prompt:
            await interaction.response.send_message(
                "아직 생성된 프롬프트가 없네. 침묵도 때로는 대답이 되지.",
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
                "마지막 프롬프트가 너무 길어서 파일로 보낼게. 긴 이야기에는 그만한 이유가 있겠지.",
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
                f"잠깐, 너무 빨라. {error.retry_after:.1f}초 후에 다시 해봐. 기다림도 하나의 미덕이니까.",
                ephemeral=True
            )
        else:
            logger.error(f"Error in command {interaction.command}: {str(error)}")
            await interaction.response.send_message(
                "뭔가 잘못됐네. 완벽한 시스템은 없다더니... 정말이야.",
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