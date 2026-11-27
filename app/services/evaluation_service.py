
import json
import logging
import re

from pathlib import Path

from app.services.embeddings_service import (
    generate_query_embedding
)

from app.services.qdrant_service import (
    search_similar_chunks
)

from app.services.rag_service import (
    build_context
)

from app.services.llm_service import (
    generate_answer,
    get_groq_client,
    GROQ_MODEL
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DATASET_PATH = (
    PROJECT_ROOT / "evaluation" / "evaluation_dataset.json"
)


def load_evaluation_dataset(
    dataset_path: Path = DEFAULT_DATASET_PATH
) -> dict:
    """
    Load the evaluation dataset from JSON.
    """

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Evaluation dataset not found: {dataset_path}"
        )

    with dataset_path.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    test_cases = dataset.get("test_cases", [])

    if not isinstance(test_cases, list) or not test_cases:
        raise ValueError(
            "Evaluation dataset contains no test cases."
        )

    return dataset


def calculate_retrieval_metrics(
    retrieved_chunks: list,
    relevant_chunk_ids: list,
    top_k: int
) -> dict:
    """
    Calculate Precision@K, Recall@K and MRR.

    Metrics are calculated only when human-labelled
    relevant chunk IDs are provided.
    """

    if not relevant_chunk_ids:
        return {
            "labelled": False,
            "precision_at_k": None,
            "recall_at_k": None,
            "reciprocal_rank": None,
            "relevant_chunks_found": None,
            "message": (
                "Add human-verified relevant_chunk_ids "
                "to calculate retrieval metrics."
            )
        }

    relevant_set = set(relevant_chunk_ids)

    retrieved_ids = [
        chunk.get("chunk_id")
        for chunk in retrieved_chunks[:top_k]
    ]

    retrieved_set = set(retrieved_ids)

    relevant_found = relevant_set.intersection(
        retrieved_set
    )

    hits = len(relevant_found)

    precision = hits / top_k if top_k else 0.0

    recall = (
        hits / len(relevant_set)
        if relevant_set else 0.0
    )

    reciprocal_rank = 0.0

    for rank, chunk_id in enumerate(retrieved_ids, start=1):

        if chunk_id in relevant_set:
            reciprocal_rank = 1.0 / rank
            break

    return {
        "labelled": True,
        "precision_at_k": round(precision, 4),
        "recall_at_k": round(recall, 4),
        "reciprocal_rank": round(reciprocal_rank, 4),
        "relevant_chunks_found": hits,
        "total_relevant_chunks": len(relevant_set)
    }


def calculate_expected_point_coverage(
    answer: str,
    expected_points: list
) -> dict:
    """
    Calculate a simple keyword/phrase coverage score.

    This is a heuristic, not a semantic correctness metric.
    """

    if not expected_points:
        return {
            "score": None,
            "matched_points": [],
            "missing_points": [],
            "message": "No expected answer points provided."
        }

    answer_lower = answer.lower()

    matched = [
        point
        for point in expected_points
        if point.lower() in answer_lower
    ]

    missing = [
        point
        for point in expected_points
        if point.lower() not in answer_lower
    ]

    score = len(matched) / len(expected_points)

    return {
        "score": round(score, 4),
        "matched_points": matched,
        "missing_points": missing
    }


def validate_citations(
    answer: str,
    retrieved_chunks: list
) -> dict:
    """
    Check whether generated source citations
    refer to retrieved source labels and pages.

    Expected citation format:
    [Source 1, Page 2]
    """

    citation_pattern = re.compile(
        r"\[Source\s+(\d+),\s*Page\s+(\d+)\]",
        re.IGNORECASE
    )

    citations = citation_pattern.findall(answer)

    valid_sources = {
        (
            index,
            str(chunk.get("page_number"))
        )
        for index, chunk in enumerate(
            retrieved_chunks,
            start=1
        )
    }

    valid = []
    invalid = []

    for source_number, page_number in citations:

        citation = (
            int(source_number),
            page_number
        )

        if citation in valid_sources:
            valid.append({
                "source_label": f"Source {source_number}",
                "page_number": int(page_number)
            })
        else:
            invalid.append({
                "source_label": f"Source {source_number}",
                "page_number": int(page_number)
            })

    return {
        "citation_count": len(citations),
        "valid_citations": valid,
        "invalid_citations": invalid,
        "all_citations_valid": len(invalid) == 0,
        "message": (
            "No citations were generated."
            if not citations
            else "Citation references checked against retrieved chunks."
        )
    }


async def evaluate_answer_with_groq(
    question: str,
    context: str,
    answer: str,
    expected_points: list
) -> dict:
    """
    Use Groq as an LLM judge to evaluate answer quality.

    Scores are on a scale of 1 to 5.
    """

    client = get_groq_client()

    evaluation_prompt = f"""
You are an independent evaluator of a
Retrieval-Augmented Generation system.

Evaluate the generated answer using ONLY
the supplied question, retrieved context
and expected answer points.

QUESTION:
{question}

RETRIEVED CONTEXT:
{context}

GENERATED ANSWER:
{answer}

EXPECTED ANSWER POINTS:
{json.dumps(expected_points, ensure_ascii=False)}

Evaluate these four dimensions:

1. faithfulness:
   Are the factual claims supported by the retrieved context?

2. answer_relevance:
   Does the answer directly address the question?

3. completeness:
   Does the answer cover the important expected points
   that are supported by the retrieved context?

4. clarity:
   Is the answer clear, understandable and well organized?

Give each score as an integer from 1 to 5.

A score of 1 means very poor.
A score of 5 means excellent.

Do not reward an answer for including unsupported
expected points. Do not treat an expected point as
ground truth if the retrieved context does not support it.

Return ONLY valid JSON in this exact structure:

{{
  "faithfulness": 1,
  "answer_relevance": 1,
  "completeness": 1,
  "clarity": 1,
  "reasoning": "Brief explanation of the evaluation.",
  "unsupported_claims": []
}}
"""

    response = await client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a strict RAG evaluation judge. "
                    "Return valid JSON only."
                )
            },
            {
                "role": "user",
                "content": evaluation_prompt
            }
        ],
        max_completion_tokens=700,
        temperature=0
    )

    raw_result = response.choices[0].message.content

    if not raw_result:
        raise RuntimeError(
            "Groq evaluation judge returned an empty response."
        )

    # Extract JSON if the model adds surrounding text.
    match = re.search(
        r"\{.*\}",
        raw_result,
        re.DOTALL
    )

    if not match:
        raise ValueError(
            "Groq evaluator did not return valid JSON."
        )

    evaluation = json.loads(match.group(0))

    score_fields = [
        "faithfulness",
        "answer_relevance",
        "completeness",
        "clarity"
    ]

    for field in score_fields:

        score = evaluation.get(field)

        if (
            not isinstance(score, int)
            or isinstance(score, bool)
            or not 1 <= score <= 5
        ):
            raise ValueError(
                f"Invalid evaluation score: {field}"
            )

    if not isinstance(
        evaluation.get("unsupported_claims"),
        list
    ):
        raise ValueError(
            "Invalid unsupported_claims field."
        )

    return evaluation


async def evaluate_single_question(
    document_id: str,
    test_case: dict,
    top_k: int = 3
) -> dict:
    """
    Evaluate retrieval and answer generation
    for one test question.
    """

    question = test_case["question"]

    logger.info(
        "Evaluating test case: %s",
        test_case.get("id")
    )

    # STEP 1: Embed question
    query_vector = generate_query_embedding(question)

    # STEP 2: Retrieve relevant chunks
    retrieved_chunks = search_similar_chunks(
        query_vector=query_vector,
        document_id=document_id,
        top_k=top_k
    )

    # STEP 3: Calculate retrieval metrics
    retrieval_metrics = calculate_retrieval_metrics(
        retrieved_chunks=retrieved_chunks,
        relevant_chunk_ids=test_case.get(
            "relevant_chunk_ids", []
        ),
        top_k=top_k
    )

    if not retrieved_chunks:

        return {
            "test_id": test_case["id"],
            "question": question,
            "status": "no_relevant_chunks",
            "retrieved_chunks": 0,
            "retrieval_metrics": retrieval_metrics,
            "answer": None,
            "answer_metrics": None,
            "citation_metrics": None
        }

    # STEP 4: Build context
    context = build_context(retrieved_chunks)

    # STEP 5: Generate answer
    answer = await generate_answer(
        question=question,
        context=context
    )

    # STEP 6: Evaluate expected point coverage
    expected_coverage = calculate_expected_point_coverage(
        answer=answer,
        expected_points=test_case.get(
            "expected_answer_points", []
        )
    )

    # STEP 7: Evaluate answer with Groq judge
    judge_result = await evaluate_answer_with_groq(
        question=question,
        context=context,
        answer=answer,
        expected_points=test_case.get(
            "expected_answer_points", []
        )
    )

    # STEP 8: Validate citations
    citation_metrics = validate_citations(
        answer=answer,
        retrieved_chunks=retrieved_chunks
    )

    return {
        "test_id": test_case["id"],
        "question": question,
        "status": "completed",
        "retrieved_chunks": len(retrieved_chunks),
        "retrieval_metrics": retrieval_metrics,
        "answer": answer,
        "answer_metrics": {
            "faithfulness": judge_result["faithfulness"],
            "answer_relevance": judge_result["answer_relevance"],
            "completeness": judge_result["completeness"],
            "clarity": judge_result["clarity"],
            "expected_point_coverage": expected_coverage,
            "reasoning": judge_result["reasoning"],
            "unsupported_claims": judge_result["unsupported_claims"]
        },
        "citation_metrics": citation_metrics
    }


async def run_rag_evaluation(
    document_id: str,
    top_k: int = 3
) -> dict:
    """
    Run the complete evaluation dataset.
    """

    dataset = load_evaluation_dataset()

    results = []

    for test_case in dataset["test_cases"]:

        try:

            result = await evaluate_single_question(
                document_id=document_id,
                test_case=test_case,
                top_k=top_k
            )

            results.append(result)

        except Exception as error:

            logger.exception(
                "Evaluation failed for test case %s",
                test_case.get("id")
            )

            results.append({
                "test_id": test_case.get("id"),
                "question": test_case.get("question"),
                "status": "failed",
                "error": str(error)
            })

    completed = [
        item
        for item in results
        if item["status"] == "completed"
    ]

    labelled_results = [
        item
        for item in completed
        if item["retrieval_metrics"]["labelled"]
    ]

    def average_metric(items, key):

        values = [
            item["retrieval_metrics"][key]
            for item in items
            if item["retrieval_metrics"][key] is not None
        ]

        return (
            round(sum(values) / len(values), 4)
            if values else None
        )

    def average_answer_score(key):

        values = [
            item["answer_metrics"][key]
            for item in completed
            if item["answer_metrics"] is not None
        ]

        return (
            round(sum(values) / len(values), 2)
            if values else None
        )

    summary = {
        "total_test_cases": len(results),
        "completed": len(completed),
        "failed": sum(
            1 for item in results
            if item["status"] == "failed"
        ),
        "no_relevant_chunks": sum(
            1 for item in results
            if item["status"] == "no_relevant_chunks"
        ),
        "labelled_retrieval_cases": len(labelled_results),
        "precision_at_k": average_metric(
            labelled_results,
            "precision_at_k"
        ),
        "recall_at_k": average_metric(
            labelled_results,
            "recall_at_k"
        ),
        "mean_reciprocal_rank": average_metric(
            labelled_results,
            "reciprocal_rank"
        ),
        "average_faithfulness": average_answer_score(
            "faithfulness"
        ),
        "average_answer_relevance": average_answer_score(
            "answer_relevance"
        ),
        "average_completeness": average_answer_score(
            "completeness"
        ),
        "average_clarity": average_answer_score(
            "clarity"
        )
    }

    return {
        "success": True,
        "document_id": document_id,
        "dataset_name": dataset.get("dataset_name"),
        "summary": summary,
        "results": results
    }
