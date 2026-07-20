#!/usr/bin/env python3
"""발표 Issue가 삭제되면 디스코드로 알린다.

삭제된 이슈는 gh API로 다시 조회할 수 없으므로, 워크플로우가 삭제 이벤트
페이로드에서 받은 제목/본문을 환경변수로 그대로 넘겨준다.
"""
import os

from lib import parse_sections, post_discord


def main() -> None:
    title = os.environ.get("ISSUE_TITLE", "(제목 없음)")
    number = os.environ.get("ISSUE_NUMBER", "?")
    body = os.environ.get("ISSUE_BODY", "")
    presenter = parse_sections(body).get("발표자", "").strip()
    who = f" ({presenter})" if presenter else ""
    post_discord(f"🗑️ **발표 취소/삭제됨**: {title}{who} (#{number})")


if __name__ == "__main__":
    main()
