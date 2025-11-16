#!/usr/bin/env python3
"""Script to view evaluation results from MongoDB."""

import argparse
from datetime import datetime
from typing import Optional

from src.utils.memory import ConversationMemory


def format_timestamp(ts):
    """Format timestamp for display."""
    if isinstance(ts, datetime):
        return ts.strftime("%Y-%m-%d %H:%M:%S")
    return str(ts)


def print_evaluation_detail(eval_doc: dict):
    """Print detailed evaluation information."""
    print("\n" + "=" * 80)
    print(f"Evaluation ID: {eval_doc['evaluation_id']}")
    print(f"Session ID: {eval_doc['session_id']}")
    print(f"User ID: {eval_doc['user_id']}")
    print(f"Status: {eval_doc['status']}")
    print(f"Created: {format_timestamp(eval_doc['created_at'])}")

    if eval_doc.get('completed_at'):
        print(f"Completed: {format_timestamp(eval_doc['completed_at'])}")

    print("\n--- User Input ---")
    print(eval_doc['user_input'])

    print("\n--- Agent Output ---")
    print(eval_doc['agent_output'])

    if eval_doc.get('context'):
        print("\n--- Context ---")
        for key, value in eval_doc['context'].items():
            print(f"  {key}: {value}")

    if eval_doc.get('scores'):
        print("\n--- Evaluation Scores ---")
        for metric, score in eval_doc['scores'].items():
            passed = eval_doc.get('metrics_passed', {}).get(metric, False)
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {metric:20s}: {score:.3f} {status}")

        overall = eval_doc.get('overall_passed', False)
        print(f"\n  Overall: {'✅ PASSED' if overall else '❌ FAILED'}")

    if eval_doc.get('critical_issues'):
        print("\n--- Critical Issues ---")
        for issue in eval_doc['critical_issues']:
            print(f"  ⚠️  {issue}")

    if eval_doc.get('error'):
        print(f"\n--- Error ---")
        print(f"  {eval_doc['error']}")

    print("=" * 80)


def print_session_summary(memory: ConversationMemory, session_id: str):
    """Print evaluation summary for a session."""
    stats = memory.evaluation_manager.get_session_statistics(session_id)

    print(f"\n{'=' * 60}")
    print(f"Session Evaluation Summary: {session_id}")
    print(f"{'=' * 60}")
    print(f"Total Evaluations: {stats['total_evaluations']}")
    print(f"Completed: {stats['completed']}")
    print(f"Pending: {stats['pending']}")
    print(f"Failed: {stats['failed']}")
    print(f"Pass Rate: {stats['pass_rate']*100:.1f}%")
    print(f"Critical Issues: {stats['critical_issues_count']}")

    if stats['average_scores']:
        print("\nAverage Scores:")
        for metric, score in stats['average_scores'].items():
            print(f"  {metric:20s}: {score:.3f}")

    print(f"{'=' * 60}\n")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="View evaluation results")
    parser.add_argument(
        "--session-id",
        help="Session ID to view evaluations for"
    )
    parser.add_argument(
        "--user-id",
        help="User ID to view statistics for"
    )
    parser.add_argument(
        "--eval-id",
        help="Specific evaluation ID to view details"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit number of results (default: 10)"
    )
    parser.add_argument(
        "--status",
        choices=["pending", "in_progress", "completed", "failed"],
        help="Filter by status"
    )
    parser.add_argument(
        "--mongodb-uri",
        default="mongodb://admin:password123@localhost:27017/",
        help="MongoDB URI"
    )
    parser.add_argument(
        "--database",
        default="loan_advisor",
        help="Database name"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary statistics only"
    )

    args = parser.parse_args()

    # Connect to MongoDB
    memory = ConversationMemory(
        mongodb_uri=args.mongodb_uri,
        database_name=args.database,
        enable_evaluation=True
    )

    try:
        # View specific evaluation
        if args.eval_id:
            eval_doc = memory.evaluation_manager.get_evaluation_result(args.eval_id)
            if eval_doc:
                print_evaluation_detail(eval_doc)
            else:
                print(f"Evaluation {args.eval_id} not found")
            return

        # View session evaluations
        if args.session_id:
            if args.summary:
                print_session_summary(memory, args.session_id)
            else:
                evaluations = memory.evaluation_manager.get_session_evaluations(
                    args.session_id,
                    limit=args.limit
                )

                if not evaluations:
                    print(f"No evaluations found for session {args.session_id}")
                    return

                print(f"\nFound {len(evaluations)} evaluations for session {args.session_id}\n")

                # Filter by status if specified
                if args.status:
                    evaluations = [e for e in evaluations if e['status'] == args.status]

                for eval_doc in evaluations:
                    print_evaluation_detail(eval_doc)

                # Also show summary
                print_session_summary(memory, args.session_id)

            return

        # View user statistics
        if args.user_id:
            stats = memory.evaluation_manager.get_user_statistics(args.user_id)

            print(f"\n{'=' * 60}")
            print(f"User Evaluation Statistics: {args.user_id}")
            print(f"{'=' * 60}")
            print(f"Total Evaluations: {stats['total_evaluations']}")
            print(f"Sessions: {stats['sessions_count']}")
            print(f"Overall Pass Rate: {stats['pass_rate']*100:.1f}%")

            if stats['average_scores']:
                print("\nAverage Scores Across All Sessions:")
                for metric, score in stats['average_scores'].items():
                    print(f"  {metric:20s}: {score:.3f}")

            print(f"{'=' * 60}\n")
            return

        # No specific filter - show recent evaluations
        print("Please specify --session-id, --user-id, or --eval-id")
        print("\nExample usage:")
        print("  python scripts/view_evaluations.py --session-id user123_20240115_143022")
        print("  python scripts/view_evaluations.py --user-id user123")
        print("  python scripts/view_evaluations.py --eval-id eval_xxx_yyy")
        print("  python scripts/view_evaluations.py --session-id xxx --summary")

    finally:
        memory.close()


if __name__ == "__main__":
    main()
