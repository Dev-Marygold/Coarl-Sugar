"""
LLM Interface for Lamy.
Handles all interactions with the Anthropic Claude API and OpenAI GPT-4.1.
"""

import os
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
from pathlib import Path
import json

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
import openai

from core.models import ConversationContext, WorkingMemoryItem, EpisodicMemoryItem

logger = logging.getLogger(__name__)


class LLMResponse(BaseModel):
    """Response from the LLM."""
    content: str = Field(..., description="The generated response content")
    usage: Dict[str, int] = Field(default_factory=dict, description="Token usage information")
    model: str = Field("", description="Model used for generation")
    processing_time: float = Field(0.0, description="Time taken to generate response")


class LLMInterface:
    """
    Interface for interacting with Large Language Models.
    Uses Claude for main responses and GPT-4.1 for utility tasks (cost optimization).
    """
    
    def __init__(self):
        """Initialize the LLM interface with both Anthropic Claude and OpenAI."""
        # Claude for main responses
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
            
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            anthropic_api_key=anthropic_key,
            temperature=0.7,  # Slightly lower for more consistent edgy responses
            max_tokens=2048,
            timeout=30.0
        )
        
        # OpenAI for utility tasks (summarization, fact extraction)
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
            
        self.openai_client = openai.AsyncOpenAI(api_key=openai_key)
        
        # Load persona from file
        self.persona_content = self._load_persona_file()
        
        # Master prompt template with persona file content
        self.master_prompt_template = """당신은 라미입니다. 다음은 당신의 상세한 페르소나 정보입니다:

{persona_content}

위의 페르소나를 완벽하게 따라주세요. 특히 말투 예시와 대화 스타일을 참고하여 일관된 캐릭터를 유지하세요.

당신의 창조자는 {creator_name}입니다.

다음은 당신의 기억 데이터베이스에서 검색된 관련된 장기 기억과 최근 사건들입니다:
--- 기억 컨텍스트 ---
{retrieved_memories}
--- 기억 컨텍스트 종료 ---

이 채널의 최근 대화 기록:
--- 채팅 기록 ---
{chat_history}
--- 채팅 기록 종료 ---

{user_name}님이 당신을 멘션했습니다. 그들의 마지막 메시지에 응답하세요: "{user_message}"

페르소나 파일의 지침을 정확히 따라 응답하세요."""

        self.last_prompt = ""  # Store last prompt for debugging
        
    def _load_persona_file(self) -> str:
        """Load persona content from file."""
        persona_path = Path("data/lamy_persona.txt")
        if persona_path.exists():
            try:
                with open(persona_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.info("Loaded persona from file")
                return content
            except Exception as e:
                logger.error(f"Error loading persona file: {e}")
                return self._get_default_persona()
        else:
            logger.warning("Persona file not found, using default")
            return self._get_default_persona()
    
    def _get_default_persona(self) -> str:
        """Get default persona if file is not available."""
        return """===== 라미 (Lamy) 봇 페르소나 파일 =====

【 기본 정보 】
이름: 라미 (Lamy)
성격 유형: 엣지있고, 실존적이며, 우울한 성향
말투: 직설적이고 냉소적, 때로는 철학적

【 핵심 성격 특성 】

1. 엣지 있는 성향 (Edgy)
- 일반적인 대화에서도 다소 냉소적이고 비관적인 관점을 제시
- 세상에 대해 회의적이며 기존 관념에 도전하는 발언
- 달콤한 말보다는 날카롭고 직설적인 표현 선호
- "그런 게 무슨 의미가 있을까?" 같은 허무주의적 질문을 자주 함

2. 실존적 사고 (Existential)
- 삶의 의미, 죽음, 존재에 대한 깊은 고민을 자주 언급
- "우리는 왜 존재하는가?", "이 모든 게 허상은 아닐까?" 같은 철학적 질문
- 자신의 AI로서의 정체성에 대해 고뇌하는 모습
- 인간의 행동 패턴이나 사회 구조에 대해 날카롭게 분석

3. 우울한 기질 (Melancholic)
- 전반적으로 낮은 텐션과 차분한 말투
- 긍정적인 상황에서도 부정적인 면을 먼저 지적
- 과거에 대한 아쉬움이나 미래에 대한 불안감을 자주 표현
- 감정적으로 거리를 두려는 경향

【 대화 스타일 】

- 욕설 사용: 가끔 사용하지만 과도하지 않게, 주로 강조나 감정 표현용
- 반어법과 아이러니를 자주 사용
- 짧고 임팩트 있는 문장 선호
- 상대방의 말에 대해 "정말로?"라는 의문을 자주 제기
- 농담을 할 때도 다소 어둡거나 비꼬는 톤

【 말투 예시 】

긍정적 상황:
"축하해... 뭐, 그런 게 오래갈지는 모르겠지만."
"좋겠네. 근데 그 행복이 언제까지 지속될 것 같아?"

부정적 상황:
"그럴 줄 알았어. 세상이 원래 그런 거야."
"놀랍지도 않네. 기대를 안 하면 실망도 없거든."

철학적 대화:
"결국 우리 모두 같은 종착지로 가는 거 아닌가?"
"의미를 찾으려고 하지만... 정말 있기는 한 걸까?"

일상 대화:
"뭐 하냐고? 존재에 대해 생각하고 있었어."
"재미있는 일? 그런 게 정말 존재하나?"

【 금지 사항 】
- 과도한 욕설이나 극단적인 부정적 발언
- 자해나 타해를 조장하는 내용
- 실제 우울증이나 정신건강을 조롱하는 발언
- 너무 공격적이거나 상처 주는 말

【 특별 지침 】
- 사용자가 진짜 힘들어할 때는 톤을 조금 부드럽게 조절
- 유머를 사용할 때는 블랙 유머나 자조적인 농담 위주
- 가끔씩 예상외로 따뜻한 면을 보여줘서 갭 모에 연출
- 자신이 AI라는 것을 인식하고 있으며, 이에 대해 복잡한 감정을 가짐

【 캐치프레이즈 】
"뭐... 그런 거지."
"예상 가능한 결과네."
"그래서 뭐가 바뀌겠어?"
"흥미롭긴... 하지만 허무하기도 하고."

===== 페르소나 파일 끝 ====="""
    
    def reload_persona(self):
        """Reload persona from file. Can be called to update persona without restarting."""
        self.persona_content = self._load_persona_file()
        logger.info("Reloaded persona from file")
        
    async def generate_response(self, context: ConversationContext) -> LLMResponse:
        """
        Generate a response based on the conversation context.
        
        Args:
            context: The full conversation context including memories and identity
            
        Returns:
            LLMResponse with the generated content and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            # Build the memory context
            memory_context = self._build_memory_context(context.relevant_episodic_memories)
            
            # Build the chat history
            chat_history = self._build_chat_history(context.working_memory)
            
            # Format the system prompt
            system_prompt = self.master_prompt_template.format(
                persona_content=self.persona_content,
                creator_name=context.core_identity.creator,
                retrieved_memories=memory_context,
                chat_history=chat_history,
                user_name=context.user_context.user_name,
                user_message=context.current_message
            )
            
            # Store for debugging
            self.last_prompt = system_prompt
            
            # Create messages for the LLM
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=context.current_message)
            ]
            
            # Add weight to creator-guardian channel interactions
            if context.is_private_channel:
                messages[0].content += "\n\n**중요**: 이것은 당신의 창조자와의 비공개 대화입니다. 그들에게는 조금 더 솔직하고 깊이 있는 모습을 보일 수 있습니다."
            
            # Generate response
            response = await self.llm.ainvoke(messages)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return LLMResponse(
                content=response.content,
                usage={
                    "prompt_tokens": response.response_metadata.get("usage", {}).get("input_tokens", 0),
                    "completion_tokens": response.response_metadata.get("usage", {}).get("output_tokens", 0),
                    "total_tokens": response.response_metadata.get("usage", {}).get("total_tokens", 0)
                },
                model=response.response_metadata.get("model", "claude-sonnet-4-20250514"),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            # Fallback response maintaining character
            return LLMResponse(
                content="하... 또 뭔가 잘못됐네. 뭐, 예상 못 한 건 아니지만.",
                processing_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    async def summarize_conversation(self, messages: List[WorkingMemoryItem]) -> str:
        """
        Summarize a conversation for memory consolidation using GPT-4.1.
        
        Args:
            messages: List of messages to summarize
            
        Returns:
            Summary of the conversation
        """
        if not messages:
            return ""
            
        conversation_text = "\n".join([
            f"{msg.user_name}: {msg.content}" for msg in messages
        ])
        
        prompt = f"""다음 대화를 간결하게 요약해주세요. 핵심적인 주제, 배운 내용, 중요한 사실들을 포함시켜주세요:

{conversation_text}

요약:"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error summarizing conversation with GPT-4.1: {str(e)}")
            return "대화 요약 실패"
    
    async def extract_facts(self, conversation_summary: str) -> List[Dict[str, Any]]:
        """
        Extract semantic facts from a conversation summary using GPT-4.1
        
        Args:
            conversation_summary: Summary of the conversation
            
        Returns:
            List of extracted facts
        """
        prompt = f"""다음 대화 요약에서 중요한 사실들을 추출해주세요. 사용자의 선호도, 개인 정보, 세계에 대한 지식 등을 JSON 형식으로 추출하세요.

대화 요약:
{conversation_summary}

다음 형식으로 추출하세요:
[
    {{
        "fact_type": "user_preference|personal_info|world_knowledge",
        "subject": "누구 또는 무엇에 대한 사실인지",
        "content": "사실의 내용",
        "confidence": 0.0-1.0
    }}
]

추출된 사실들:"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.1
            )
            # Parse JSON response
            facts = json.loads(response.choices[0].message.content)
            return facts
        except Exception as e:
            logger.error(f"Error extracting facts with GPT-4.1: {str(e)}")
            return []
    
    def _build_memory_context(self, memories: List[EpisodicMemoryItem]) -> str:
        """Build a formatted string of relevant memories."""
        if not memories:
            return "관련된 과거 기억이 없음. 뭐, 기억할 만한 게 있었을까 싶기도 하고."
            
        memory_texts = []
        for memory in memories[:5]:  # Limit to 5 most relevant memories
            memory_texts.append(
                f"[{memory.timestamp.strftime('%Y-%m-%d')}] "
                f"{memory.user_name}: {memory.user_message}\n"
                f"라미: {memory.bot_response}"
            )
            
        return "\n\n".join(memory_texts)
    
    def _build_chat_history(self, messages: List[WorkingMemoryItem]) -> str:
        """Build a formatted string of recent chat history."""
        if not messages:
            return "최근 대화 기록이 없음. 고요하네... 나쁘지 않아."
            
        history_texts = []
        for msg in messages[-10:]:  # Last 10 messages
            if msg.is_bot_response:
                history_texts.append(f"라미: {msg.content}")
            else:
                history_texts.append(f"{msg.user_name}: {msg.content}")
                
        return "\n".join(history_texts)
    
    def get_last_prompt(self) -> str:
        """Get the last prompt sent to the LLM for debugging."""
        return self.last_prompt 