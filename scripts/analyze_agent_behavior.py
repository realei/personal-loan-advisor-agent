#!/usr/bin/env python
"""完整的Agent行为分析工具 - 展示工具调用、Metrics和MongoDB存储"""

import sys
import json
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.loan_advisor_agent import loan_advisor_agent

def analyze_agent_response(query):
    """分析Agent响应的完整信息"""

    print("=" * 60)
    print("🤖 Agent行为分析")
    print("=" * 60)
    print(f"\n📝 输入问题: {query}\n")

    # 运行Agent
    response = loan_advisor_agent.run(query, stream=False)

    # 1. 工具调用分析
    print("\n" + "=" * 60)
    print("🔧 工具调用链")
    print("=" * 60)

    tool_sequence = []
    tool_results = {}

    for i, msg in enumerate(response.messages):
        # Assistant调用工具
        if msg.role == 'assistant' and msg.tool_calls:
            for tool_call in msg.tool_calls:
                tool_name = tool_call['function']['name']
                tool_args = json.loads(tool_call['function']['arguments'])
                tool_id = tool_call['id']

                tool_sequence.append({
                    'name': tool_name,
                    'args': tool_args,
                    'id': tool_id
                })

                print(f"\n调用 {len(tool_sequence)}: {tool_name}")
                print(f"参数:")
                for key, value in tool_args.items():
                    print(f"  - {key}: {value}")

        # Tool返回结果
        elif msg.role == 'tool':
            if tool_sequence:
                last_tool = tool_sequence[-1]
                result_preview = str(msg.content)[:200] if msg.content else "无内容"
                tool_results[last_tool['id']] = result_preview
                print(f"结果预览: {result_preview}...")

    # 2. Metrics分析
    print("\n" + "=" * 60)
    print("📊 性能指标 (Metrics)")
    print("=" * 60)

    if hasattr(response, 'metrics'):
        metrics = response.metrics.to_dict()
        print(f"Token使用:")
        print(f"  - 输入: {metrics.get('input_tokens', 0)}")
        print(f"  - 输出: {metrics.get('output_tokens', 0)}")
        print(f"  - 总计: {metrics.get('total_tokens', 0)}")

        if 'duration_ns' in metrics and metrics['duration_ns']:
            duration_s = metrics['duration_ns'] / 1e9
            print(f"\n响应时间: {duration_s:.2f} 秒")
            print(f"Tokens/秒: {metrics.get('total_tokens', 0) / duration_s:.1f}")

    # 3. 会话级Metrics
    session_metrics = loan_advisor_agent.get_session_metrics()
    if session_metrics:
        s_metrics = session_metrics.to_dict()
        print(f"\n会话累计:")
        print(f"  - 总Tokens: {s_metrics.get('total_tokens', 0)}")

    # 4. MongoDB存储说明
    print("\n" + "=" * 60)
    print("💾 MongoDB存储")
    print("=" * 60)

    if loan_advisor_agent.db:
        print("✅ MongoDB已配置，数据自动存储到:")
        print(f"  - 数据库: loan_advisor")
        print(f"  - 会话集合: agno_sessions")
        print(f"  - 记忆集合: agno_memories")
        print(f"  - 指标集合: agno_metrics")
        print(f"\n当前会话ID: {loan_advisor_agent.session_id}")
    else:
        print("⚠️  MongoDB未配置，数据仅在内存中")

    # 5. 最终答案
    print("\n" + "=" * 60)
    print("💬 最终回答")
    print("=" * 60)
    print(response.content[:500] + "..." if len(response.content) > 500 else response.content)

    return {
        'tool_sequence': tool_sequence,
        'metrics': metrics if 'metrics' in locals() else {},
        'content': response.content
    }

if __name__ == "__main__":
    # 测试复杂查询（会调用多个工具）
    test_query = "我35岁，月收入8000美元，信用分720，债务1000美元。想贷款5万美元36个月，帮我检查资格、计算月供，并评估是否负担得起"

    result = analyze_agent_response(test_query)

    print("\n" + "=" * 60)
    print("✅ 分析完成")
    print("=" * 60)
    print(f"\n工具调用次数: {len(result['tool_sequence'])}")
    print(f"总Token消耗: {result['metrics'].get('total_tokens', 0)}")