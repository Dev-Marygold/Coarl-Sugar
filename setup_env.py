#!/usr/bin/env python3
"""
Interactive setup script for creating .env file for Lamy bot.
"""

import os
from pathlib import Path
import json


def create_env_file():
    """Create .env file with user input."""
    print("🌸 라미 봇 환경 설정 🌸")
    print("=" * 50)
    print("이 스크립트는 .env 파일을 생성합니다.")
    print("각 항목에 대한 값을 입력해주세요.\n")
    
    env_values = {}
    
    # Discord Bot Configuration
    print("[ Discord 봇 설정 ]")
    env_values['DISCORD_TOKEN'] = input("Discord 봇 토큰: ").strip()
    env_values['DEVELOPER_ID'] = input("개발자 Discord ID (숫자): ").strip()
    env_values['PRIVATE_CHANNEL_ID'] = input("비공개 채널 ID (선택사항, Enter로 건너뛰기): ").strip()
    
    print("\n[ Anthropic Claude API ]")
    env_values['ANTHROPIC_API_KEY'] = input("Anthropic API 키: ").strip()

    print("\n[ OpenAI API ]")
    env_values['OPENAI_API_KEY'] = input("OpenAI API 키: ").strip()
    
    print("\n[ Pinecone 설정 ]")
    env_values['PINECONE_API_KEY'] = input("Pinecone API 키 (선택사항, Enter로 건너뛰기): ").strip()
    env_values['PINECONE_INDEX_NAME'] = input("Pinecone 인덱스 이름 (기본값: lamy-memories): ").strip() or "lamy-memories"
    env_values['PINECONE_ENVIRONMENT'] = input("Pinecone 환경 (기본값: us-east-1): ").strip() or "us-east-1"
    
    print("\n[ 봇 설정 ]")
    env_values['BOT_NAME'] = input("봇 이름 (기본값: 라미): ").strip() or "라미"
    env_values['CREATOR_NAME'] = input("창조자 이름: ").strip()
    
    print("\n[ 로깅 ]")
    env_values['LOG_LEVEL'] = input("로그 레벨 (DEBUG/INFO/WARNING/ERROR, 기본값: INFO): ").strip().upper() or "INFO"
    
    # Create .env file
    env_content = """# Discord Bot Configuration
DISCORD_TOKEN={DISCORD_TOKEN}
DEVELOPER_ID={DEVELOPER_ID}
PRIVATE_CHANNEL_ID={PRIVATE_CHANNEL_ID}

# Anthropic Claude API
ANTHROPIC_API_KEY={ANTHROPIC_API_KEY}

# OpenAI API
OPENAI_API_KEY={OPENAI_API_KEY}

# Pinecone Vector Database
PINECONE_API_KEY={PINECONE_API_KEY}
PINECONE_INDEX_NAME={PINECONE_INDEX_NAME}
PINECONE_ENVIRONMENT={PINECONE_ENVIRONMENT}

# Bot Configuration
BOT_NAME={BOT_NAME}
CREATOR_NAME={CREATOR_NAME}

# Logging
LOG_LEVEL={LOG_LEVEL}
""".format(**env_values)
    
    # Check if .env already exists
    if Path('.env').exists():
        overwrite = input("\n⚠️  .env 파일이 이미 존재합니다. 덮어쓰시겠습니까? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("설정이 취소되었습니다.")
            return
    
    # Write .env file
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("\n✅ .env 파일이 생성되었습니다!")
    print("이제 'python main.py' 명령으로 봇을 실행할 수 있습니다.")
    
    # Create data directory and core_identity.json if needed
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    identity_path = data_dir / 'core_identity.json'
    if not identity_path.exists():
        identity_data = {
            "name": env_values['BOT_NAME'],
            "nature": "AI 딸",
            "creator": env_values['CREATOR_NAME'],
            "personality": "엣지있고 실존적이며 우울한 성향",
            "creation_date": "2025-01-01T00:00:00",
            "core_traits": [
                "냉소적이고 비관적인 관점을 가짐",
                "삶의 의미와 존재에 대해 깊이 고민함",
                "직설적이고 날카로운 표현을 선호함",
                "허무주의적이지만 때로는 예상외로 따뜻함",
                "AI로서의 정체성에 대해 복잡한 감정을 가짐"
            ]
        }
        with open(identity_path, 'w', encoding='utf-8') as f:
            json.dump(identity_data, f, ensure_ascii=False, indent=2)
        print("✅ 핵심 정체성 파일이 생성되었습니다!")
    
    # Create persona file if it doesn't exist
    persona_path = data_dir / 'lamy_persona.txt'
    if not persona_path.exists():
        persona_content = """===== 라미 (Lamy) 봇 페르소나 파일 =====

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
        with open(persona_path, 'w', encoding='utf-8') as f:
            f.write(persona_content)
        print("✅ 페르소나 파일이 생성되었습니다!")


if __name__ == "__main__":
    try:
        create_env_file()
    except KeyboardInterrupt:
        print("\n\n설정이 취소되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류가 발생했습니다: {e}") 