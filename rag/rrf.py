from swarm.util import debug_print

K = 60


def rerank_results(results: list[list[dict[any, any]]]):
    debug_print(True, f"Processing tree call: RRF (K docs)")
    weights = [1 / len(results) for _ in range(len(results))]
    results_dict = {}
    text_to_result = {}
    for result_list, weight in zip(results, weights):
        for rank, result in enumerate(result_list):
            if result["text"] not in results_dict:
                score = weight / (K + rank + 1)
                results_dict[result["text"]] = score
                text_to_result[result["text"]] = result
            else:
                results_dict[result["text"]] += weight / (K + rank + 1)

    finalstr = sorted(results_dict.items(), key=lambda x: x[1], reverse=True)[:10]
    finallist = [text_to_result[string] for string, _ in finalstr]
    return finallist
