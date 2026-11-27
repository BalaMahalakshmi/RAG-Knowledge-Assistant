
import asyncio

from app.services.llm_service import generate_answer


async def main():

    question = "What is supervised learning?"

    context = """
    Supervised learning is a type of machine learning
    in which a model learns from labelled training data.

    The training dataset contains input examples
    and their corresponding correct outputs.
    """

    print("=" * 60)
    print("GROQ CONNECTION TEST")
    print("=" * 60)

    print("\nQuestion:")
    print(question)

    print("\nSending request to Groq...")

    answer = await generate_answer(
        question=question,
        context=context
    )

    print("\nGenerated Answer:")
    print("-" * 60)
    print(answer)

    print("\nGroq test completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
