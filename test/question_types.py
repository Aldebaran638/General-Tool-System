from typing import Literal, NotRequired, TypedDict


class Question(TypedDict):
    """统一题目结构。"""
    type: Literal["single", "multiple", "judgment"]
    stem: str
    options: list[str]
    answer: str | list[str]
    analysis: NotRequired[str]


def create_single_choice(
    stem: str,
    options: list[str],
    answer: str,
    analysis: str = "",
) -> Question:
    """创建单选题。"""
    return {
        "type": "single",
        "stem": stem,
        "options": options,
        "answer": answer,
        **({"analysis": analysis} if analysis else {}),
    }


def create_multiple_choice(
    stem: str,
    options: list[str],
    answer: list[str],
    analysis: str = "",
) -> Question:
    """创建多选题。"""
    return {
        "type": "multiple",
        "stem": stem,
        "options": options,
        "answer": answer,
        **({"analysis": analysis} if analysis else {}),
    }


def create_judgment(
    stem: str,
    answer: bool,
    options: list[str] | None = None,
    analysis: str = "",
) -> Question:
    """创建判断题。默认选项为 ["正确", "错误"]，answer 用 bool 传入。"""
    return {
        "type": "judgment",
        "stem": stem,
        "options": options if options is not None else ["正确", "错误"],
        "answer": "正确" if answer else "错误",
        **({"analysis": analysis} if analysis else {}),
    }


if __name__ == "__main__":
    q1 = create_single_choice(
        stem="Python 的创始人是谁？",
        options=["Guido van Rossum", "Linus Torvalds", "Bill Gates"],
        answer="Guido van Rossum",
        analysis="Python 由 Guido 于 1991 年发布。",
    )

    q2 = create_multiple_choice(
        stem="以下哪些是 Python 的数据类型？",
        options=["int", "str", "list", "class"],
        answer=["int", "str", "list"],
    )

    q3 = create_judgment(
        stem="Python 是编译型语言。",
        answer=False,
    )

    print(q1)
    print(q2)
    print(q3)
