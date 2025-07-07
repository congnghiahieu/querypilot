import json
import random

import numpy as np

from src.nl2sql.utils.linking_utils.application import mask_question_with_schema_linking
from src.nl2sql.utils.utils import jaccard_similarity


class BasicExampleSelector:
    def __init__(self, data, *args, **kwargs):
        self.data = data
        self.train_json_file = "train_json.json"
        self.train_questions_file = "train_questions.txt"

        # Try to load train_json from file, if not found get from data and save
        try:
            print("Loading train_json from file...")
            with open(self.train_json_file) as f:
                self.train_json = json.load(f)
            print("Successfully loaded train_json from file")
        except FileNotFoundError:
            print("train_json file not found, getting from data...")
            self.train_json = self.data.get_train_json()
            print("Saving train_json to file...")
            with open(self.train_json_file, "w") as f:
                json.dump(self.train_json, f)
            print("Successfully saved train_json to file")

        # Try to load train_questions from file, if not found get from data and save
        try:
            print("Loading train_questions from file...")
            with open(self.train_questions_file) as f:
                self.train_questions = f.read().splitlines()
            print("Successfully loaded train_questions from file")
        except FileNotFoundError:
            print("train_questions file not found, getting from data...")
            self.train_questions = self.data.get_train_questions()
            print("Saving train_questions to file...")
            with open(self.train_questions_file, "w") as f:
                f.write("\n".join(self.train_questions))
            print("Successfully saved train_questions to file")

        self.db_ids = [d["db_id"] for d in self.train_json]

    def get_examples(self, question, num_example, cross_domain=False):
        pass

    def domain_mask(self, candidates: list, db_id):
        cross_domain_candidates = [
            candidates[i] for i in range(len(self.db_ids)) if self.db_ids[i] != db_id
        ]
        return cross_domain_candidates

    def retrieve_index(self, indexes: list, db_id):
        cross_domain_indexes = [i for i in range(len(self.db_ids)) if self.db_ids[i] != db_id]
        retrieved_indexes = [cross_domain_indexes[i] for i in indexes]
        return retrieved_indexes


class RandomExampleSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data)
        random.seed(0)

    def get_examples(self, target, num_example, cross_domain=False):
        train_json = self.train_json
        indexes = list(range(len(train_json)))
        if cross_domain:
            indexes = domain_mask(indexes, target["db_id"])
        selected_indexes = random.sample(indexes, num_example)
        if cross_domain:
            selected_indexes = retrieve_index(selected_indexes, target["db_id"])
        return [train_json[index] for index in selected_indexes]


class CosineSimilarExampleSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data)

        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"
        # self.SELECT_MODEL = "sentence-transformers/bert-base-nli-mean-tokens"

        from sentence_transformers import SentenceTransformer

        self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
        self.train_embeddings = self.bert_model.encode(self.train_questions)

    def get_examples(self, target, num_example, cross_domain=False):
        target_embedding = self.bert_model.encode([target["question"]])
        # target_embedding = self.bert_model.embed_text([target["question"]]).cpu().detach().numpy()

        # find the most similar question in train dataset
        from sklearn.metrics.pairwise import cosine_similarity

        similarities = np.squeeze(
            cosine_similarity(target_embedding, self.train_embeddings)
        ).tolist()
        pairs = [
            (similarity, index)
            for similarity, index in zip(similarities, range(len(similarities)), strict=False)
        ]

        train_json = self.train_json
        pairs_sorted = sorted(pairs, key=lambda x: x[0], reverse=True)
        top_pairs = list()
        for s, index in pairs_sorted:
            similar_db_id = train_json[index]["db_id"]
            if cross_domain and similar_db_id == target["db_id"]:
                continue
            if train_json[index]["question"] == target["question"]:
                continue
            top_pairs.append((index, s))
            if len(top_pairs) >= num_example:
                break

        return [train_json[index] for (index, s) in top_pairs]


class EuclideanDistanceExampleSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data)

        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"

        from sentence_transformers import SentenceTransformer

        self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
        self.train_embeddings = self.bert_model.encode(self.train_questions)

    def get_examples(self, target, num_example, cross_domain=False):
        target_embedding = self.bert_model.encode([target["question"]])

        # find the most similar question in train dataset
        from sklearn.metrics.pairwise import euclidean_distances

        distances = np.squeeze(
            euclidean_distances(target_embedding, self.train_embeddings)
        ).tolist()
        pairs = [
            (distance, index)
            for distance, index in zip(distances, range(len(distances)), strict=False)
        ]

        train_json = self.train_json
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        top_pairs = list()
        for d, index in pairs_sorted:
            similar_db_id = train_json[index]["db_id"]
            if cross_domain and similar_db_id == target["db_id"]:
                continue
            top_pairs.append((index, d))
            if len(top_pairs) >= num_example:
                break

        return [train_json[index] for (index, d) in top_pairs]


class EuclideanDistanceThresholdExampleSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data)

        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"
        # self.top_distances = list()
        self.threshold = 0.85

        from sentence_transformers import SentenceTransformer

        self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
        self.train_embeddings = self.bert_model.encode(self.train_questions)

    def get_examples(self, target, num_example, cross_domain=False):
        target_embedding = self.bert_model.encode([target["question"]])

        # find the most similar question in train dataset
        from sklearn.metrics.pairwise import euclidean_distances

        distances = np.squeeze(
            euclidean_distances(target_embedding, self.train_embeddings)
        ).tolist()
        pairs = [
            (distance, index)
            for distance, index in zip(distances, range(len(distances)), strict=False)
        ]

        train_json = self.train_json
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        top_pairs = list()
        for d, index in pairs_sorted:
            similar_db_id = train_json[index]["db_id"]
            if (cross_domain and similar_db_id == target["db_id"]) or d > self.threshold:
                continue
            top_pairs.append((index, d))
            # self.top_distances.append(d)
            if len(top_pairs) >= num_example:
                break
        # print("mean", np.mean(self.top_distances))    # 0.822
        # print("std", np.std(self.top_distances, ddof=1))  # 0.144
        # print("max", max(self.top_distances)) # 1.166

        return [train_json[index] for (index, d) in top_pairs]


class EuclideanDistanceSkeletonSimilarThresholdSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data)

        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"
        self.threshold = 0.85
        self.mask_token = "<mask>"  # the "<mask>" is the mask token of all-mpnet-base-v2
        self.value_token = "<unk>"  # the "<unk>" is the unknown token of all-mpnet-base-v2

        from sentence_transformers import SentenceTransformer

        train_mask_questions = mask_question_with_schema_linking(
            self.train_json, mask_tag=self.mask_token, value_tag=self.value_token
        )
        self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
        self.train_embeddings = self.bert_model.encode(train_mask_questions)

    def get_examples(self, target, num_example, cross_domain=False):
        target_mask_question = mask_question_with_schema_linking(
            [target], mask_tag=self.mask_token, value_tag=self.value_token
        )
        target_embedding = self.bert_model.encode(target_mask_question)

        # find the most similar question in train dataset
        from sklearn.metrics.pairwise import euclidean_distances

        distances = np.squeeze(
            euclidean_distances(target_embedding, self.train_embeddings)
        ).tolist()
        pairs = [
            (distance, index)
            for distance, index in zip(distances, range(len(distances)), strict=False)
        ]

        train_json = self.train_json
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        top_pairs = list()
        for d, index in pairs_sorted:
            similar_db_id = train_json[index]["db_id"]
            if cross_domain and similar_db_id == target["db_id"]:
                continue
            # Skeleton similarity
            if (
                jaccard_similarity(train_json[index]["query_skeleton"], target["query_skeleton"])
                < self.threshold
            ):
                continue
            top_pairs.append((index, d))
            if len(top_pairs) >= num_example:
                break

        if len(top_pairs) < num_example:
            for d, index in pairs_sorted:
                similar_db_id = train_json[index]["db_id"]
                if cross_domain and similar_db_id == target["db_id"]:
                    continue
                # Skeleton similarity
                if (
                    jaccard_similarity(
                        train_json[index]["query_skeleton"], target["query_skeleton"]
                    )
                    >= self.threshold
                ):
                    continue
                top_pairs.append((index, d))
                if len(top_pairs) >= num_example:
                    break

        return [train_json[index] for (index, d) in top_pairs]


class EuclideanDistanceQuestionMaskSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        print("start init selector")
        super().__init__(data)
        print("end init selector")

        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"
        self.mask_token = "<mask>"  # the "<mask>" is the mask token of all-mpnet-base-v2
        self.value_token = "<unk>"  # the "<unk>" is the unknown token of all-mpnet-base-v2
        self.embeddings_file = "train_embeddings.npy"

        from sentence_transformers import SentenceTransformer

        print("start loading bert model")
        train_mask_questions = mask_question_with_schema_linking(
            self.train_json, mask_tag=self.mask_token, value_tag=self.value_token
        )
        self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")

        # Try to load embeddings from file, if not found compute and save them
        try:
            print("Loading embeddings from file...")
            self.train_embeddings = np.load(self.embeddings_file)
            print("Successfully loaded embeddings from file")
        except FileNotFoundError:
            print("Embeddings file not found, computing embeddings...")
            self.train_embeddings = self.bert_model.encode(train_mask_questions)
            print("Saving embeddings to file...")
            np.save(self.embeddings_file, self.train_embeddings)
            print("Successfully saved embeddings to file")

    def get_examples(self, target, num_example, cross_domain=False):
        target_mask_question = mask_question_with_schema_linking(
            [target], mask_tag=self.mask_token, value_tag=self.value_token
        )
        target_embedding = self.bert_model.encode(target_mask_question)

        # find the most similar question in train dataset
        from sklearn.metrics.pairwise import euclidean_distances

        distances = np.squeeze(
            euclidean_distances(target_embedding, self.train_embeddings)
        ).tolist()
        pairs = [
            (distance, index)
            for distance, index in zip(distances, range(len(distances)), strict=False)
        ]

        train_json = self.train_json
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        top_pairs = list()
        for d, index in pairs_sorted:
            similar_db_id = train_json[index]["db_id"]
            if cross_domain and similar_db_id == target["db_id"]:
                continue
            top_pairs.append((index, d))
            if len(top_pairs) >= num_example:
                break

        return [train_json[index] for (index, d) in top_pairs]


class EuclideanDistancePreSkeletonSimilarThresholdSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data)

        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"
        self.threshold = 0.85

        from sentence_transformers import SentenceTransformer

        self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
        self.train_embeddings = self.bert_model.encode(self.train_questions)

    def get_examples(self, target, num_example, cross_domain=False):
        target_embedding = self.bert_model.encode([target["question"]])

        # find the most similar question in train dataset
        from sklearn.metrics.pairwise import euclidean_distances

        distances = np.squeeze(
            euclidean_distances(target_embedding, self.train_embeddings)
        ).tolist()
        pairs = [
            (distance, index)
            for distance, index in zip(distances, range(len(distances)), strict=False)
        ]

        train_json = self.train_json
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        top_pairs = list()
        for d, index in pairs_sorted:
            similar_db_id = train_json[index]["db_id"]
            if cross_domain and similar_db_id == target["db_id"]:
                continue
            # Skeleton similarity
            if (
                jaccard_similarity(train_json[index]["pre_skeleton"], target["pre_skeleton"])
                < self.threshold
            ):
                continue
            top_pairs.append((index, d))
            if len(top_pairs) >= num_example:
                break

        if len(top_pairs) < num_example:
            for d, index in pairs_sorted:
                similar_db_id = train_json[index]["db_id"]
                if cross_domain and similar_db_id == target["db_id"]:
                    continue
                # Skeleton similarity
                if (
                    jaccard_similarity(train_json[index]["pre_skeleton"], target["pre_skeleton"])
                    >= self.threshold
                ):
                    continue
                top_pairs.append((index, d))
                if len(top_pairs) >= num_example:
                    break

        return [train_json[index] for (index, d) in top_pairs]


class EuclideanDistancePreSkeletonSimilarPlusSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data)

        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"

        from sentence_transformers import SentenceTransformer

        self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
        self.train_embeddings = self.bert_model.encode(self.train_questions)

    def get_examples(self, target, num_example, cross_domain=False):
        target_embedding = self.bert_model.encode([target["question"]])

        # find the most similar question in train dataset
        from sklearn.metrics.pairwise import euclidean_distances

        distances = np.squeeze(
            euclidean_distances(target_embedding, self.train_embeddings)
        ).tolist()
        train_json = self.train_json
        for i in range(len(train_json)):
            distances[i] -= jaccard_similarity(
                train_json[i]["pre_skeleton"], target["pre_skeleton"]
            )
        pairs = [
            (distance, index)
            for distance, index in zip(distances, range(len(distances)), strict=False)
        ]
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        top_pairs = list()
        for d, index in pairs_sorted:
            similar_db_id = train_json[index]["db_id"]
            if cross_domain and similar_db_id == target["db_id"]:
                continue
            top_pairs.append((index, d))
            if len(top_pairs) >= num_example:
                break

        return [train_json[index] for (index, d) in top_pairs]


class EuclideanDistanceQuestionMaskPreSkeletonSimilarThresholdSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data)

        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"
        self.mask_token = "<mask>"  # the "<mask>" is the mask token of all-mpnet-base-v2
        self.value_token = "<unk>"  # the "<unk>" is the unknown token of all-mpnet-base-v2
        self.threshold = 0.85

        from sentence_transformers import SentenceTransformer

        train_mask_questions = mask_question_with_schema_linking(
            self.train_json, mask_tag=self.mask_token, value_tag=self.value_token
        )
        self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
        self.train_embeddings = self.bert_model.encode(train_mask_questions)

    def get_examples(self, target, num_example, cross_domain=False):
        target_mask_question = mask_question_with_schema_linking(
            [target], mask_tag=self.mask_token, value_tag=self.value_token
        )
        target_embedding = self.bert_model.encode(target_mask_question)

        # find the most similar question in train dataset
        from sklearn.metrics.pairwise import euclidean_distances

        distances = np.squeeze(
            euclidean_distances(target_embedding, self.train_embeddings)
        ).tolist()
        pairs = [
            (distance, index)
            for distance, index in zip(distances, range(len(distances)), strict=False)
        ]

        train_json = self.train_json
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        top_pairs = list()
        for d, index in pairs_sorted:
            similar_db_id = train_json[index]["db_id"]
            if cross_domain and similar_db_id == target["db_id"]:
                continue
            # Skeleton similarity
            if (
                jaccard_similarity(train_json[index]["pre_skeleton"], target["pre_skeleton"])
                < self.threshold
            ):
                continue
            top_pairs.append((index, d))
            if len(top_pairs) >= num_example:
                break

        if len(top_pairs) < num_example:
            for d, index in pairs_sorted:
                similar_db_id = train_json[index]["db_id"]
                if cross_domain and similar_db_id == target["db_id"]:
                    continue
                # Skeleton similarity
                if (
                    jaccard_similarity(train_json[index]["pre_skeleton"], target["pre_skeleton"])
                    >= self.threshold
                ):
                    continue
                top_pairs.append((index, d))
                if len(top_pairs) >= num_example:
                    break

        return [train_json[index] for (index, d) in top_pairs]


class EuclideanDistanceQuestionMaskPreSkeletonSimilarThresholdShiftSelector(BasicExampleSelector):
    def __init__(self, data, *args, **kwargs):
        super().__init__(data)

        self.SELECT_MODEL = "sentence-transformers/all-mpnet-base-v2"
        self.mask_token = "<mask>"  # the "<mask>" is the mask token of all-mpnet-base-v2
        self.value_token = "<unk>"  # the "<unk>" is the unknown token of all-mpnet-base-v2
        self.threshold = 0.85

        from sentence_transformers import SentenceTransformer

        train_mask_questions = mask_question_with_schema_linking(
            self.train_json, mask_tag=self.mask_token, value_tag=self.value_token
        )
        self.bert_model = SentenceTransformer(self.SELECT_MODEL, device="cpu")
        self.train_embeddings = self.bert_model.encode(train_mask_questions)

    def get_examples(self, target, num_example, cross_domain=False):
        target_mask_question = mask_question_with_schema_linking(
            [target], mask_tag=self.mask_token, value_tag=self.value_token
        )
        target_embedding = self.bert_model.encode(target_mask_question)

        # find the most similar question in train dataset
        from sklearn.metrics.pairwise import euclidean_distances

        distances = np.squeeze(
            euclidean_distances(target_embedding, self.train_embeddings)
        ).tolist()
        pairs = [
            (distance, index)
            for distance, index in zip(distances, range(len(distances)), strict=False)
        ]

        train_json = self.train_json
        pairs_sorted = sorted(pairs, key=lambda x: x[0])
        top_pairs = list()
        for d, index in pairs_sorted:
            similar_db_id = train_json[index]["db_id"]
            if cross_domain and similar_db_id == target["db_id"]:
                continue
            # Skeleton similarity
            if (
                jaccard_similarity(train_json[index]["pre_skeleton"], target["pre_skeleton"])
                < self.threshold
            ):
                continue
            top_pairs.append((index, d))
            if len(top_pairs) >= num_example:
                break

        return [train_json[index] for (index, d) in top_pairs]
