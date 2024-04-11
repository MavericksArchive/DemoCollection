import random
from InputExample import InputExample


class MSMARCODataset(Dataset):
    def __init__(self, queries, corpus, ce_scores):
        self.queries = queries
        self.queries_ids = list(queries.keys())
        self.corpus = corpus
        self.ce_scores = ce_scores

        for qid in self.queries:
            self.queries[qid]["pos"] = list(self.queries[qid]["pos"])
            self.queries[qid]["neg"] = list(self.queries[qid]["neg"])
            random.shuffle(self.queries[qid]["neg"])

    def __getitem__(self, item):
        query = self.queries[self.queries_ids[item]]
        query_text = query["query"]
        qid = query["qid"]

        if len(query["pos"]) > 0:
            pos_id = query["pos"].pop(0)  # Pop positive and add at end
            pos_text = self.corpus[pos_id]
            query["pos"].append(pos_id)
        else:  # We only have negatives, use two negs
            pos_id = query["neg"].pop(0)  # Pop negative and add at end
            pos_text = self.corpus[pos_id]
            query["neg"].append(pos_id)

        # Get a negative passage
        neg_id = query["neg"].pop(0)  # Pop negative and add at end
        neg_text = self.corpus[neg_id]
        query["neg"].append(neg_id)

        pos_score = self.ce_scores[qid][pos_id]
        neg_score = self.ce_scores[qid][neg_id]

        return InputExample(texts=[query_text, pos_text, neg_text], label=pos_score - neg_score)

    def __len__(self):
        return len(self.queries)
