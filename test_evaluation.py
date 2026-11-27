
import asyncio
import json

from pathlib import Path

from app.services.evaluation_service import (
    run_rag_evaluation
)


async def main():

    document_id = (
        "0782bb757295485fa19dfec29435ceeb"
    )

    print("=" * 70)
    print("RAG KNOWLEDGE ASSISTANT - EVALUATION")
    print("=" * 70)

    report = await run_rag_evaluation(
        document_id=document_id,
        top_k=3
    )

    print("\nEVALUATION SUMMARY")
    print("-" * 70)

    print(
        json.dumps(
            report["summary"],
            indent=4
        )
    )

    print("\nINDIVIDUAL TEST RESULTS")
    print("-" * 70)

    for result in report["results"]:

        print(f"\nTest ID: {result['test_id']}")
        print(f"Question: {result['question']}")
        print(f"Status: {result['status']}")

        if result["status"] == "completed":

            print("\nGenerated Answer:")
            print(result["answer"])

            print("\nAnswer Metrics:")
            print(
                json.dumps(
                    result["answer_metrics"],
                    indent=4
                )
            )

            print("\nCitation Metrics:")
            print(
                json.dumps(
                    result["citation_metrics"],
                    indent=4
                )
            )

        elif result["status"] == "failed":

            print("Error:", result["error"])

    # Save evaluation report
    report_directory = Path("evaluation/reports")
    report_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    report_path = (
        report_directory / "latest_evaluation.json"
    )

    report_path.write_text(
        json.dumps(
            report,
            indent=4,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print("\n" + "=" * 70)
    print("EVALUATION COMPLETED")
    print(f"Report saved to: {report_path}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
