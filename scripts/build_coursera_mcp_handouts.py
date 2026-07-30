#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
COURSE_DIR = ROOT / "coursera-mcp"
COURSE_TITLE_CN = "模型上下文协议导论"
COURSE_TITLE_EN = "Introduction to Model Context Protocol"


def clean(text: str) -> str:
    return dedent(text).strip()


def itemize(items: list[str]) -> str:
    return "\n".join(["\\begin{itemize}", *[f"  \\item {item}" for item in items], "\\end{itemize}"])


def make_summary(opening: str, paragraphs: list[str], bullets: list[str]) -> str:
    parts = [rf"\textbf{{本讲重点：}} {opening}"]
    parts.extend(paragraphs)
    if bullets:
        parts.append(itemize(bullets))
    return "\n\n".join(parts)


def mcq(question: str, *options: str) -> dict[str, object]:
    return {"q": question, "options": list(options)}


def rich_block(
    summary: str,
    *,
    diagram: list[str] | None = None,
    visual_notes: list[str] | None = None,
    discussion: list[str] | None = None,
    key_points: list[str] | None = None,
) -> dict[str, object]:
    block: dict[str, object] = {"summary": summary}
    if key_points:
        block["key_points"] = key_points
    if diagram:
        block["diagram"] = diagram
    if visual_notes:
        block["visual_notes"] = visual_notes
    if discussion:
        block["discussion"] = discussion
    return block


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


MODULES = {
    1: {
        "unit_title_cn": "第一单元：认识 MCP",
        "unit_title_en": "Module 1: Getting Started with MCP",
        "module_url": "https://www.coursera.org/learn/introduction-to-model-context-protocol/home/module/1",
        "lectures": [
            {
                "stem": "01_welcome-to-the-course",
                "title_cn": "欢迎与课程路线图",
                "title_en": "Welcome to the Course",
                "summary": rich_block(
                    make_summary(
                    "先建立课程地图，再明确学习前提。",
                    [
                        clean(
                            r"""
                            这一讲不是先写代码，而是先把整门课的路线图铺开：你会先理解 MCP 要解决什么问题，
                            再拆开 client 和 server 的职责，最后进入 tools、resources、prompts 三类服务器能力。
                            """
                        ),
                        clean(
                            r"""
                            讲者同时交代了学习前提：需要基础 Python、本地运行环境，以及后面会用到的 uv-cli。
                            把环境准备好，后面的动手部分才不会被琐碎问题打断。
                            """
                        ),
                    ],
                    [
                        "先知道这门课要解决什么，再进入实现细节。",
                        "本课程会把概念、协议和动手项目结合起来。",
                        "准备好 Python 和 uv-cli 是进入实操阶段的前提。",
                    ],
                    ),
                    diagram=[
                        "课程路线图",
                        "问题 -> 协议 -> client / server -> tools / resources / prompts",
                        "先看全局，再进入实现。",
                    ],
                    visual_notes=[
                        "留意课程先讲问题，再讲代码。",
                        "如果幻灯片上出现路线图，先抓箭头和顺序。",
                    ],
                    discussion=[
                        "为什么讲义一开始要先给路线图，而不是先贴代码？",
                        "如果直接进入实现，最容易丢掉哪一层的理解？",
                    ],
                ),
            },
            {
                "stem": "02_introducing-mcp",
                "title_cn": "认识 MCP",
                "title_en": "Introducing MCP",
                "summary": rich_block(
                    make_summary(
                    "MCP 是连接模型与外部能力的标准通信层。",
                    [
                        clean(
                            r"""
                            这一讲用 GitHub 聊天机器人的例子说明：如果每次都手写 API 调用、拼接上下文、处理权限，
                            工程会迅速变得凌乱。MCP 的价值就是把这些重复工作抽象成统一协议。
                            """
                        ),
                        clean(
                            r"""
                            在这个框架里，server 不只是“一个后端”，它还可以把 tools、resources、prompts
                            统一暴露出来，让应用和模型通过标准方式协作。
                            """
                        ),
                    ],
                    [
                        "tools 负责让模型执行明确动作，比如查询 Pull Request。",
                        "resources 负责把数据送进上下文。",
                        "prompts 负责把可复用的指令模板交给应用或用户。",
                    ],
                    ),
                    diagram=[
                        "App -> Client -> MCP Server -> GitHub / 外部服务",
                        "MCP 负责标准通信层，不负责替代模型本身。",
                    ],
                    visual_notes=[
                        "看图时先找 client 和 server 的边界。",
                        "把 tools / resources / prompts 看成三种可暴露的能力。",
                    ],
                    discussion=[
                        "为什么把这些能力包进一个标准协议，比每个应用自己写一套更省心？",
                        "如果工具越来越多，标准接口会帮你减少什么重复劳动？",
                    ],
                ),
            },
            {
                "stem": "03_mcp-clients",
                "title_cn": "MCP 客户端",
                "title_en": "MCP Clients",
                "summary": rich_block(
                    make_summary(
                    "client 是通信入口，transport 可以有多种实现。",
                    [
                        clean(
                            r"""
                            MCP 并不强制一种传输协议：同机时可以走 stdin/stdout，分布式时也可以走 HTTP 或
                            WebSockets。客户端负责把应用请求翻译成协议消息，再把 server 的响应交回上层。
                            """
                        ),
                        clean(
                            r"""
                            这一讲还点出了几个关键消息类型，比如 \texttt{ListToolsRequest}、
                            \texttt{ListToolsResult} 和 \texttt{CallToolRequest}。理解这些消息，
                            才能看懂 client 和 server 之间到底交换了什么。
                            """
                        ),
                    ],
                    [
                        "client 不是能力本身，而是访问 server 的入口。",
                        "协议定义了消息类型和交互方式。",
                        "同一个 server 可以被不同应用复用。",
                    ],
                    ),
                    diagram=[
                        "应用请求",
                        "   -> client 翻译成协议消息",
                        "   -> server 处理并返回结果",
                        "   -> 应用拿到响应",
                    ],
                    visual_notes=[
                        "重点看 client 是怎么把应用语言翻译成协议语言的。",
                        "把 ListToolsRequest / CallToolRequest 和返回结果对上号。",
                    ],
                    discussion=[
                        "为什么 transport 可以变化，但消息语义不变？",
                        "如果 client 只负责翻译，那它应该尽量轻还是尽量重？",
                    ],
                ),
            },
        ],
        "overview": clean(
            r"""
            这一单元先回答一个最根本的问题：为什么需要 MCP。
            它把“模型如何安全、稳定地接入外部能力”变成一个标准协议，
            也把应用、client、server 的职责分开，避免把 API 调用直接硬塞进提示词里。
            """
        )
        + "\n\n"
        + itemize(
            [
                "理解 MCP 解决的是“连接层”问题，而不是替代模型本身。",
                "认识 client / server 的分工。",
                "初步建立 tools、resources、prompts 这三类原语的直觉。",
            ]
        ),
        "knowledge_map": [
            {"topic": "MCP 是什么", "question": "它如何把模型和外部能力连接起来？"},
            {"topic": "Client / Server", "question": "谁负责通信，谁负责暴露能力？"},
            {"topic": "三类原语", "question": "tools、resources、prompts 各自解决什么问题？"},
        ],
        "key_takeaways": [
            "MCP 是一个标准通信层，不是单一模型或框架。",
            "Client 负责连接与转发，Server 负责暴露能力。",
            "Tools、resources、prompts 是 server 的三类原语。",
            "传输层可以是 stdio、HTTP、WebSockets 等。",
            "先理解协议，再写代码，会更容易看懂后面的项目。",
        ],
        "exercises": {
            "choice": [
                mcq("MCP 最核心的作用是什么？", "A. 代替 Python 解释器", "B. 让模型和外部能力用统一协议通信", "C. 生成 UI 组件", "D. 自动训练模型"),
                mcq("MCP server 通常暴露哪三类能力？", "A. 变量、类、函数", "B. 文件、网络、数据库", "C. tools、resources、prompts", "D. 终端、浏览器、IDE"),
                mcq("课程示例中的应用主要想让模型访问什么？", "A. GitHub 数据", "B. 本地相册", "C. 股票行情", "D. 邮件附件"),
                mcq("为什么说 MCP 是 transport agnostic？", "A. 只能用 HTTP", "B. 只支持同机进程", "C. 可通过多种协议通信", "D. 必须走数据库"),
                mcq("ListToolsRequest 的作用是什么？", "A. 创建工具", "B. 请求服务器列出可用工具", "C. 发送提示词", "D. 下载资源"),
            ],
            "truefalse": [
                "Client 负责把服务器能力暴露给模型。",
                "同一机器上的 client 和 server 可以通过 stdin/stdout 通信。",
                "MCP 不需要明确的消息类型。",
            ],
            "shortanswer": [
                "用自己的话解释 client 和 server 的分工。",
                "为什么 GitHub 聊天机器人适合用 MCP 来实现？",
            ],
        },
        "answers": {
            "choice": "1.B \\quad 2.C \\quad 3.A \\quad 4.C \\quad 5.B",
            "truefalse": "1. 错 \\quad 2. 对 \\quad 3. 错",
            "shortanswer": [
                "Client 负责建立连接、发送请求和接收响应；Server 负责把工具、资源和提示词等能力暴露出来。",
                "因为 GitHub 场景需要稳定地访问外部 API 和上下文，MCP 可以把这些能力标准化并复用。",
            ],
        },
        "synthesis": rich_block(
            clean(
                r"""
                第一单元的主线是：先把 MCP 当成连接层，再把 client / server / primitive 的分工拆清楚。
                只要这张图建立起来，后面的实现细节就不会散。
                """
            )
            + "\n\n"
            + itemize(
                [
                    "先看协议层，再看实现层。",
                    "client 是翻译器，server 是能力出口。",
                    "tools、resources、prompts 是三种不同的暴露方式。",
                ]
            ),
            diagram=[
                "模型 / 应用",
                "   -> client",
                "   -> server",
                "   -> 外部服务",
            ],
            visual_notes=[
                "先看谁发请求，再看谁负责执行。",
                "如果图里有三层边界，就先把边界记住。",
            ],
        ),
        "discussion": rich_block(
            clean(
                r"""
                从今天的角度看，MCP 的价值不只是在于“能接工具”，更在于它让接口边界更清楚。
                这会直接影响后面每一个应用如何组织代码。
                """
            )
            + "\n\n"
            + itemize(
                [
                    "如果一个场景长期要接很多外部服务，标准协议会比手写集成更稳。",
                    "如果 client 变得太重，协议层的好处会被削弱。",
                ]
            ),
            discussion=[
                "当外部能力越来越多时，你更希望自己维护哪一层，哪一层尽量标准化？",
                "如果你的应用后来要换 transport，哪些设计会最先受影响？",
            ],
        ),
    },
    2: {
        "unit_title_cn": "第二单元：搭建服务器与工具",
        "unit_title_en": "Module 2: Setting Up the Server and Tools",
        "module_url": "https://www.coursera.org/learn/introduction-to-model-context-protocol/home/module/2",
        "lectures": [
            {
                "stem": "01_project-setup",
                "title_cn": "项目搭建",
                "title_en": "Project Setup",
                "summary": rich_block(
                    make_summary(
                    "先把练习项目搭起来，再往里填 MCP 逻辑。",
                    [
                        clean(
                            r"""
                            这一讲启动了一个 CLI 聊天机器人项目，用它来观察 client 和 server 如何真正协作。
                            项目里会用到一组存放在内存中的文档，方便我们把注意力集中在 MCP 的结构，而不是持久化细节。
                            """
                        ),
                        clean(
                            r"""
                            这个设计的好处是：你可以一边在终端里聊天，一边逐步把服务器能力补进去，
                            每一个新功能都能马上看到效果。
                            """
                        ),
                    ],
                    [
                        "这是一个练习性质的 CLI 聊天机器人，而不是完整产品。",
                        "文档先放在内存里，便于快速迭代。",
                        "项目目标是让你看到 client 和 server 如何协同工作。",
                    ],
                    ),
                    diagram=[
                        "CLI 聊天机器人",
                        "   -> 内存文档",
                        "   -> 逐步补上 MCP 逻辑",
                    ],
                    visual_notes=[
                        "看清楚这里先搭的是骨架，不是最终产品。",
                        "如果页面在强调内存文档，重点是降低复杂度。",
                    ],
                    discussion=[
                        "为什么先做一个最小可运行项目，比直接写完整功能更适合教学？",
                    ],
                ),
            },
            {
                "stem": "02_defining-tools-with-mcp",
                "title_cn": "使用 MCP 定义工具",
                "title_en": "Defining Tools with MCP",
                "summary": rich_block(
                    make_summary(
                    "开始给 server 增加两个最基础的 tool。",
                    [
                        clean(
                            r"""
                            讲者在 \texttt{mcpserver.py} 里准备了一个基础 MCP server，
                            接下来要补上的就是两个工具：读取文档和更新文档。
                            这一步的重点不是语法炫技，而是理解 tool 是 server 暴露出来、供模型调用的能力。
                            """
                        ),
                        clean(
                            r"""
                            这个单元还提醒你，MCP tool 的定义通常要带上清晰的输入输出结构；
                            从工程角度看，这就是把“能做什么”和“怎么调用”拆成可验证的接口。
                            """
                        ),
                    ],
                    [
                        "先实现 read / update 这样的基础能力。",
                        "工具代码放在 \texttt{mcpserver.py} 中。",
                        "JSON schema 让工具接口更明确、可检查。",
                    ],
                    ),
                    diagram=[
                        "Tool 定义",
                        "输入 schema -> function -> 输出结果",
                        "把“能做什么”和“怎么调用”拆开。",
                    ],
                    visual_notes=[
                        "留意 schema 和实现是分开的两件事。",
                        "如果幻灯片出现输入输出框，先记输入字段。",
                    ],
                    discussion=[
                        "为什么工具接口越清晰，后面的调试就越省事？",
                        "如果把输入输出写得含糊，模型会怎么误用它？",
                    ],
                ),
            },
            {
                "stem": "03_the-server-inspector",
                "title_cn": "服务器 Inspector",
                "title_en": "The Server Inspector",
                "summary": rich_block(
                    make_summary(
                    "用 Inspector 把 server 的行为看清楚。",
                    [
                        clean(
                            r"""
                            这一讲介绍如何运行 \texttt{mcp dev}，再在浏览器里打开 MCP inspector。
                            这套工具把调试回路缩短了：你能直接连接 server，切换资源、提示词和工具标签页，
                            观察它到底返回了什么。
                            """
                        ),
                        clean(
                            r"""
                            讲者也提醒，Inspector 仍在快速演进，所以界面细节可能变化。
                            但核心思路不会变：先连上 server，再逐项验证能力是否符合预期。
                            """
                        ),
                    ],
                    [
                        "Inspector 是验证 server 是否按预期工作的调试面板。",
                        "它能帮助你尽早发现工具定义或返回值的问题。",
                        "把开发、测试和修正连成一个短闭环很重要。",
                    ],
                    ),
                    diagram=[
                        "写工具",
                        "   -> mcp dev",
                        "   -> Inspector 检查",
                        "   -> 修改并复测",
                    ],
                    visual_notes=[
                        "看清楚 Inspector 的作用是把调试回路缩短。",
                        "如果界面里有多个标签页，关注资源、提示词和工具的切换。",
                    ],
                    discussion=[
                        "为什么调试面板能帮助你更快发现协议实现的问题？",
                    ],
                ),
            },
        ],
        "overview": clean(
            r"""
            这一单元进入动手阶段，围绕一个 CLI 聊天机器人项目搭建 MCP server 并验证工具。
            核心目标不是写出炫技代码，而是把“定义能力 -> 运行调试 -> 修正实现”的闭环建立起来。
            """
        )
        + "\n\n"
        + itemize(
            [
                "先用一个小项目把 MCP 落地。",
                "工具是 server 暴露给模型的可调用动作。",
                "Inspector 能让你快速检查 server 的实际行为。",
            ]
        ),
        "knowledge_map": [
            {"topic": "练习项目", "question": "为什么要先做一个 CLI 聊天机器人？"},
            {"topic": "工具定义", "question": "read / update 文档分别对应什么操作？"},
            {"topic": "调试闭环", "question": "Inspector 在开发流程里扮演什么角色？"},
        ],
        "key_takeaways": [
            "项目先行，概念才能落地。",
            "tools 是 server 端最直接的能力暴露方式。",
            "mcp dev + Inspector 构成了很实用的调试闭环。",
            "把文档放进内存可以暂时降低复杂度。",
            "清晰的接口比复杂的实现更重要。",
        ],
        "exercises": {
            "choice": [
                mcq("本单元要做的项目是什么？", "A. 画图应用", "B. CLI 聊天机器人", "C. 视频播放器", "D. 电子表格"),
                mcq("服务器先实现哪两个 tool？", "A. read / update document", "B. search / delete", "C. summarize / translate", "D. login / logout"),
                mcq("mcp dev 的用途是什么？", "A. 运行前端", "B. 启动 Inspector 调试 server", "C. 编译文档", "D. 安装依赖"),
                mcq("Inspector 能帮助你做什么？", "A. 只看日志", "B. 测试资源、提示词和工具", "C. 写前端样式", "D. 训练模型"),
                mcq("项目中的文档最初存放在哪里？", "A. 远程数据库", "B. 内存", "C. 浏览器 localStorage", "D. GitHub"),
            ],
            "truefalse": [
                "这个项目一开始就依赖完整的持久化存储。",
                "工具是 server 侧实现出来、供模型调用的能力。",
                "Inspector 的目标之一是帮你验证工具返回值是否符合预期。",
            ],
            "shortanswer": [
                "为什么课程会选择先做一个小型 CLI 项目？",
                "Inspector 能帮你发现哪些类别的问题？",
            ],
        },
        "answers": {
            "choice": "1.B \\quad 2.A \\quad 3.B \\quad 4.B \\quad 5.B",
            "truefalse": "1. 错 \\quad 2. 对 \\quad 3. 对",
            "shortanswer": [
                "因为小项目能把 MCP 的抽象概念压缩到一个可观察的工程场景里，便于理解 client 和 server 的配合。",
                "它可以帮助检查工具定义、返回数据结构、连接状态以及 server 是否按预期响应。",
            ],
        },
        "synthesis": rich_block(
            clean(
                r"""
                第二单元的主线不是“写很多代码”，而是把一个最小项目、工具定义和调试面板串成一个开发闭环。
                """
            )
            + "\n\n"
            + itemize(
                [
                    "先把项目跑起来，再补协议能力。",
                    "工具定义要清楚，Inspector 才有意义。",
                    "开发和验证最好形成短回路。",
                ]
            ),
            diagram=[
                "项目骨架 -> 工具实现 -> Inspector -> 修正",
            ],
            visual_notes=[
                "看图时重点抓住调试闭环。",
            ],
        ),
        "discussion": rich_block(
            clean(
                r"""
                这类实操单元最重要的是让抽象概念落到可观察的工程行为上。
                """
            )
            + "\n\n"
            + itemize(
                [
                    "如果没有调试面板，工具实现的问题会更难定位。",
                    "把文档暂时放进内存，是为了让注意力集中在协议本身。",
                ]
            ),
            discussion=[
                "如果你要把这个练习项目扩成真正产品，第一步会先补哪一层？",
            ],
        ),
    },
    3: {
        "unit_title_cn": "第三单元：客户端、资源与提示词",
        "unit_title_en": "Module 3: Client, Resources, and Prompts",
        "module_url": "https://www.coursera.org/learn/introduction-to-model-context-protocol/home/module/3",
        "lectures": [
            {
                "stem": "01_implementing-a-client",
                "title_cn": "实现 MCP 客户端",
                "title_en": "Implementing a Client",
                "summary": rich_block(
                    make_summary(
                    "把 server 侧能力接回 client，完成真正的往返调用。",
                    [
                        clean(
                            r"""
                            这一讲开始实现 \texttt{client.py} 里的 MCP client 类。它会把 client session 包起来，
                            让应用可以稳定地和 server 建立连接、发消息、收结果。
                            """
                        ),
                        clean(
                            r"""
                            讲者特别提醒：这个类还负责收尾清理，所以它不是单纯的“发请求对象”，
                            而是应用和外部 server 之间的生命周期管理者。
                            """
                        ),
                    ],
                    [
                        "client session 是真实连接的核心。",
                        "client 代码比 server 更像应用基础设施的一部分。",
                        "连接管理和资源清理不能省。",
                    ],
                    ),
                    diagram=[
                        "应用",
                        "   -> client session",
                        "   -> server",
                        "   -> 返回结果",
                    ],
                    visual_notes=[
                        "重点看 client session 不是普通请求对象。",
                        "连接、发送、收尾是一个整体。",
                    ],
                    discussion=[
                        "为什么客户端代码往往更像基础设施，而不是业务逻辑？",
                    ],
                ),
            },
            {
                "stem": "02_defining-resources",
                "title_cn": "定义资源",
                "title_en": "Defining Resources",
                "summary": rich_block(
                    make_summary(
                    "resources 让应用把上下文数据主动送给模型。",
                    [
                        clean(
                            r"""
                            这一讲增加了一个很典型的交互：用户输入 \texttt{@} 时，界面显示可引用的文档；
                            用户选中文档后，应用会把该文档内容自动插入到发给 Claude 的 prompt 里。
                            """
                        ),
                        clean(
                            r"""
                            这说明 resources 更像“应用控制的数据注入层”：它不是等模型自己去调用 tool，
                            而是由应用先把合适的上下文准备好，再送进模型。
                            """
                        ),
                    ],
                    [
                        "资源配合 \texttt{@} 自动补全，体验会更自然。",
                        "资源的内容会被插入 prompt，而不是让模型自己猜。",
                        "这是 app-controlled 的典型例子。",
                    ],
                    ),
                    diagram=[
                        "用户输入 @",
                        "   -> 应用列出可引用文档",
                        "   -> 选中文档后注入上下文",
                    ],
                    visual_notes=[
                        "看清楚资源是由应用主动注入，而不是模型临时去查。",
                        "如果页面里出现 @ 自动补全，重点是上下文入口。",
                    ],
                    discussion=[
                        "为什么把资源做成应用控制的注入层，能让体验更自然？",
                    ],
                ),
            },
            {
                "stem": "03_accessing-resources",
                "title_cn": "访问资源",
                "title_en": "Accessing Resources",
                "summary": make_summary(
                    "client 需要主动向 server 取回资源内容。",
                    [
                        clean(
                            r"""
                            在定义完资源之后，client 侧就要补上读取逻辑：给定一个 resource URI，
                            发出请求、拿到响应，并根据 MIME type 把数据解析成应用能继续使用的形式。
                            """
                        ),
                        clean(
                            r"""
                            这一步的意义在于把“资源”真正变成可消费的上下文，而不是只停留在 server 的名词定义上。
                            """
                        ),
                    ],
                    [
                        "client 需要知道如何按 URI 拉取资源。",
                        "不同 MIME type 需要不同的解析方式。",
                        "资源要最终变成 prompt 的一部分，才算真正用起来。",
                    ],
                ),
            },
            {
                "stem": "04_defining-prompts",
                "title_cn": "定义提示词",
                "title_en": "Defining Prompts",
                "summary": rich_block(
                    make_summary(
                    "prompts 让用户用 slash command 触发可复用模板。",
                    [
                        clean(
                            r"""
                            这一讲引入 \texttt{/} 开头的命令，例如 \texttt{format}。用户一旦选择某个命令，
                            应用就会把对应 prompt 当作一个可复用的操作模板来执行。
                            """
                        ),
                        clean(
                            r"""
                            和 resources 不同，prompts 更强调“用户主动选择要执行什么”，因此它更接近
                            交互式 UI 里的命令面板或菜单。
                            """
                        ),
                    ],
                    [
                        "slash command 是 prompts 的自然入口。",
                        "prompts 适合做模板化、可复用的动作。",
                        "它更像用户控制的操作，而不是模型自动触发的动作。",
                    ],
                    ),
                    diagram=[
                        "用户输入 /",
                        "   -> 命令面板",
                        "   -> 选择 prompt 模板",
                        "   -> 生成消息流",
                    ],
                    visual_notes=[
                        "留意 prompt 是用户主动选择的。",
                        "如果图里像菜单或命令面板，那就是 prompts 的入口。",
                    ],
                    discussion=[
                        "为什么 prompts 更适合做固定模板，而不是动态决策？",
                    ],
                ),
            },
            {
                "stem": "05_prompts-in-the-client",
                "title_cn": "在客户端使用提示词",
                "title_en": "Prompts in the Client",
                "summary": rich_block(
                    make_summary(
                    "把 prompt 的发现和调用接到 client 里。",
                    [
                        clean(
                            r"""
                            最后一个任务是实现 \texttt{list\_prompts} 和 \texttt{get\_prompt}：
                            前者列出 server 提供的 prompt，后者把 prompt 名称和参数传进去，
                            再把返回的 messages 交给 Claude。
                            """
                        ),
                        clean(
                            r"""
                            这样一来，client 就不只是能拉资源，也能把模板化提示词真正接到应用交互里。
                            用户在终端里看到的 slash command，背后其实就是这套消息流。
                            """
                        ),
                    ],
                    [
                        r"\texttt{list\_prompts} 负责发现 server 提供了哪些 prompt。",
                        r"\texttt{get\_prompt} 负责把参数插值进 prompt。",
                        "返回的 messages 可以直接喂给 Claude 继续对话。",
                    ],
                    ),
                    diagram=[
                        "list_prompts",
                        "   -> 发现可用模板",
                        "get_prompt",
                        "   -> 参数插值",
                        "   -> messages 进入对话",
                    ],
                    visual_notes=[
                        "看清楚发现和调用是两步。",
                        "如果图里有参数框，就留意模板如何被填充。",
                    ],
                    discussion=[
                        "resources 和 prompts 都会影响上下文，但它们的触发权为什么不同？",
                    ],
                ),
            },
        ],
        "overview": clean(
            r"""
            这一单元把 server 侧能力接回客户端，完成 resource 和 prompt 的读取、注入与交互。
            你会看到 MCP 不只是“把模型接到工具”，更是把应用里的上下文流转做成可组合的接口。
            """
        )
        + "\n\n"
        + itemize(
            [
                "client session 管理连接与清理。",
                "resources 适合做应用控制的数据注入。",
                "prompts 适合做用户控制的可复用模板。",
            ]
        ),
        "knowledge_map": [
            {"topic": "Client session", "question": "它为什么不仅仅是一个请求对象？"},
            {"topic": "资源注入", "question": r"为什么 \texttt{@} 能改善上下文输入？"},
            {"topic": "Prompt 调用", "question": "list / get prompt 分别承担什么职责？"},
        ],
        "key_takeaways": [
            "client session 负责管理与 server 的真实连接。",
            "resources 负责把上下文数据插入 prompt。",
            "prompts 让用户通过 slash command 触发模板。",
            "client 侧要补齐读取资源与调用 prompt 的能力。",
            "MCP 的重点之一是把上下文流转拆成清晰的接口。",
        ],
        "exercises": {
            "choice": [
                mcq("MCP client 中的 client session 主要负责什么？", "A. 保存 UI 主题", "B. 管理与 server 的连接和清理", "C. 生成 prompt 模板", "D. 存储文档正文"),
                mcq("resources 的设计目标是什么？", "A. 让用户输入 @ 时自动引用文档并注入上下文", "B. 让模型训练参数", "C. 让 server 自己写日志", "D. 让 UI 更花哨"),
                mcq(r"\texttt{@} 触发的功能是什么？", "A. 自动删除文件", "B. 显示可引用文档列表并插入内容", "C. 创建 prompt", "D. 启动 Inspector"),
                mcq("prompts 更像什么？", "A. 用户控制的 slash commands", "B. 随机种子", "C. 数据库 schema", "D. 网络协议"),
                mcq(r"\texttt{get\_prompt} 返回的通常是什么？", "A. 文件路径", "B. 一段 HTML", "C. 要直接喂给 Claude 的 messages", "D. 图片数组"),
            ],
            "truefalse": [
                "resources 的内容是由应用主动注入到 prompt 中的。",
                "prompts 更接近用户主动触发的操作。",
                r"\texttt{get\_prompt} 的返回值通常会直接进入后续对话流程。",
            ],
            "shortanswer": [
                r"为什么文档资源适合通过 \texttt{@} 这种交互方式引入？",
                "说明 resources 和 prompts 的区别。",
            ],
        },
        "answers": {
            "choice": "1.B \\quad 2.A \\quad 3.B \\quad 4.A \\quad 5.C",
            "truefalse": "1. 对 \\quad 2. 对 \\quad 3. 对",
            "shortanswer": [
                "因为它可以把“引用文档”变成很自然的输入动作，随后由应用自动补足上下文。",
                "resources 由应用决定何时取用并注入数据；prompts 由用户决定何时触发一个模板化操作。",
            ],
        },
        "synthesis": rich_block(
            clean(
                r"""
                第三单元把“上下文如何流动”讲完整了：client 负责连接，resources 负责注入，prompts 负责模板化调用。
                """
            )
            + "\n\n"
            + itemize(
                [
                    "client 是连接和收尾的那一层。",
                    "resources 适合把文档送进上下文。",
                    "prompts 适合让用户选择固定模板。",
                ]
            ),
            diagram=[
                "client session",
                "   -> resources 注入",
                "   -> prompts 调用",
                "   -> Claude 对话",
            ],
            visual_notes=[
                "把这一单元当成上下文流转图来记。",
            ],
        ),
        "discussion": rich_block(
            clean(
                r"""
                如果把资源和提示词看成两种不同的上下文入口，就更容易理解它们为什么都重要。
                """
            )
            + "\n\n"
            + itemize(
                [
                    "资源更像应用主动补上下文。",
                    "提示词更像用户主动选动作。",
                    "两者都在帮模型看到更合适的上下文。",
                ]
            ),
            discussion=[
                "如果你想让一个应用既能自动补上下文，又能让用户手动触发模板，应该怎么分工？",
            ],
        ),
    },
    4: {
        "unit_title_cn": "第四单元：课程回顾",
        "unit_title_en": "Module 4: Review",
        "module_url": "https://www.coursera.org/learn/introduction-to-model-context-protocol/home/module/4",
        "lectures": [
            {
                "stem": "01_mcp-review",
                "title_cn": "MCP 回顾",
                "title_en": "MCP Review",
                "summary": rich_block(
                    make_summary(
                    "把三类原语收束成一个选择框架。",
                    [
                        clean(
                            """
                            这一讲重新回顾 tools、resources、prompts 的差别，并强调一个最重要的判断方法：
                            看看到底是谁在决定它什么时候被调用。
                            """
                        ),
                        clean(
                            """
                            如果是模型在决定，就更像 tools；如果是应用在决定，就更像 resources；
                            如果是用户在决定，就更像 prompts。这个判断框架比死记术语更有用。
                            """
                        ),
                    ],
                    [
                        "tools 是 model-controlled。",
                        "resources 是 app-controlled。",
                        "prompts 是 user-controlled。",
                    ],
                    ),
                    diagram=[
                        "触发权",
                        "  model -> tools",
                        "  app -> resources",
                        "  user -> prompts",
                    ],
                    visual_notes=[
                        "把这一讲当成全课总图来读。",
                        "如果图里有三条路径，先记谁在触发。",
                    ],
                    discussion=[
                        "为什么“先看触发权”比“先背术语”更稳？",
                    ],
                ),
            }
        ],
        "overview": clean(
            """
            最后一单元把整门课收束到一个简单但实用的判断框架：当能力应该由模型决定时用 tools，
            当能力应该由应用决定时用 resources，当能力应该由用户决定时用 prompts。
            """
        )
        + "\n\n"
        + itemize(
            [
                "先问“谁来触发”，再问“该用哪种原语”。",
                "这一套分类能直接指导应用设计。",
                "MCP 的价值在于把能力暴露方式讲清楚。",
            ]
        ),
        "knowledge_map": [
            {"topic": "控制方", "question": "谁决定 tool / resource / prompt 什么时候被调用？"},
            {"topic": "选型规则", "question": "什么场景该用哪种原语？"},
            {"topic": "回顾目标", "question": "整门课最终想建立什么判断框架？"},
        ],
        "key_takeaways": [
            "tools 是 model-controlled。",
            "resources 是 app-controlled。",
            "prompts 是 user-controlled。",
            "选择原语时先看触发权归谁。",
            "MCP 的核心价值是让能力暴露方式清晰、统一、可复用。",
        ],
        "exercises": {
            "choice": [
                mcq("tools 属于哪种控制方式？", "A. model-controlled", "B. app-controlled", "C. user-controlled", "D. OS-controlled"),
                mcq("resources 属于哪种控制方式？", "A. model-controlled", "B. app-controlled", "C. user-controlled", "D. 随机控制"),
                mcq("prompts 属于哪种控制方式？", "A. model-controlled", "B. app-controlled", "C. user-controlled", "D. 网络控制"),
                mcq("如果你想让应用根据用户点击来触发一段固定指令模板，优先用什么？", "A. tools", "B. prompts", "C. resources", "D. database"),
                mcq("MCP 的一个重要价值是什么？", "A. 让每个应用都写一套私有协议", "B. 把能力暴露方式结构化", "C. 取消 client", "D. 只支持一种传输"),
            ],
            "truefalse": [
                "选择原语时，先判断由谁来决定它被触发。",
                "resources 更适合应用主动注入上下文数据。",
                "prompts 的触发权通常在用户手里。",
            ],
            "shortanswer": [
                "分别用一句话概括 tools、resources、prompts 的职责。",
                "举一个你会优先使用 resources 而不是 tools 的场景。",
            ],
        },
        "answers": {
            "choice": "1.A \\quad 2.B \\quad 3.C \\quad 4.B \\quad 5.B",
            "truefalse": "1. 对 \\quad 2. 对 \\quad 3. 对",
            "shortanswer": [
                "tools 由模型决定何时调用；resources 由应用决定何时提供上下文；prompts 由用户决定何时触发模板。",
                "例如用户引用一份文档并希望自动把内容注入上下文时，更适合用 resources。",
            ],
        },
        "synthesis": rich_block(
            clean(
                """
                第四单元把整门课压成一个最实用的判断：先看谁触发，再看该用哪种原语。
                """
            )
            + "\n\n"
            + itemize(
                [
                    "model 触发 tools。",
                    "app 触发 resources。",
                    "user 触发 prompts。",
                ]
            ),
            diagram=[
                "触发权 -> 原语选择",
                "model -> tools",
                "app -> resources",
                "user -> prompts",
            ],
            visual_notes=[
                "这张图适合作为全课结尾的复习页。",
            ],
        ),
        "discussion": rich_block(
            clean(
                """
                如果把最新官方修订放进这张图里看，MCP 正在朝着更轻的状态管理、更清晰的发现机制，以及更统一的订阅处理方向走。
                这些变化不改变这门课的主线，但会让实现层更简单。
                """
            )
            + "\n\n"
            + itemize(
                [
                    "更少的会话状态，会让 client 更轻。",
                    "更统一的发现与订阅方式，会让协议更像一套清楚的消息流。",
                    "从学习角度看，最新修订强化的还是“触发权 -> 原语选择”的主线。",
                ]
            ),
            discussion=[
                "如果协议越来越轻，client 和 server 的边界会怎样重新变清楚？",
                "从这门课回看最新修订，最值得记住的变化方向是什么？",
            ],
        ),
    },
}


def build_module(module_num: int, module: dict[str, object]) -> None:
    module_dir = COURSE_DIR / f"module-{module_num}"
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "frames").mkdir(exist_ok=True)

    manifest = []
    for lecture in module["lectures"]:
        manifest.append(
            {
                "title": lecture["title_cn"],
                "title_en": lecture["title_en"],
                "lesson": module["unit_title_cn"],
                "lesson_en": module["unit_title_en"],
                "page_url": module["module_url"],
                "video": f'{lecture["stem"]}.mp4',
            }
        )

    content = {
        "overview": module["overview"],
        "knowledge_map": module["knowledge_map"],
        "lectures": {lecture["stem"]: lecture["summary"] for lecture in module["lectures"]},
        "synthesis": module.get("synthesis", ""),
        "discussion": module.get("discussion", ""),
        "key_takeaways": module["key_takeaways"],
        "exercises": module["exercises"],
        "answers": module["answers"],
    }

    write_json(module_dir / "manifest.json", manifest)
    write_json(module_dir / "content.json", content)

    tex_path = module_dir / "handout.tex"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_handout.py"),
            "--data-dir",
            str(module_dir),
            "--course-title",
            COURSE_TITLE_CN,
            "--unit-title",
            module["unit_title_cn"],
            "--course-title-en",
            COURSE_TITLE_EN,
            "--unit-title-en",
            module["unit_title_en"],
            "--lang",
            "zh",
            "--output",
            str(tex_path),
        ],
        check=True,
        cwd=ROOT,
    )

    for _ in range(2):
        subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
            check=True,
            cwd=module_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def build_index() -> None:
    lines = ["# Coursera MCP Handouts", ""]
    for module_num, module in MODULES.items():
        lines.append(f"- [Module {module_num} PDF](module-{module_num}/handout.pdf)")
    (COURSE_DIR / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    COURSE_DIR.mkdir(exist_ok=True)
    for module_num, module in MODULES.items():
        build_module(module_num, module)
    build_index()
    print(f"Built handouts under {COURSE_DIR}")


if __name__ == "__main__":
    main()
