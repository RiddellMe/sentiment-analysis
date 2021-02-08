import logging
import re
from collections import defaultdict
from concurrent import futures
from enum import Enum
from typing import List

import numpy as np
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ClassificationData(BaseModel):
    comment: str
    classification: int


class DocumentClass(BaseModel):
    prior: float
    word_frequency = defaultdict(float)
    log_likelihood = {}


class NaiveBayes:
    regex = re.compile(r'\W+')
    _ADD_ALPHA_SMOOTHING: int
    vocabulary_frequency = defaultdict(int)
    document_frequency = defaultdict(int)
    negative_class: DocumentClass
    positive_class: DocumentClass
    test_results: List[ClassificationData]

    def __init__(self, add_alpha_smoothing: int = 1, words_to_ignore: List[str] = None):
        self.filters = words_to_ignore
        self._ADD_ALPHA_SMOOTHING = add_alpha_smoothing

    class Mode(Enum):
        COUNT = "count"
        FREQ = "frequency"

    def convert_from_list(self, data: List[List]) -> List[ClassificationData]:
        results = []
        for raw_data in data:
            results.append(ClassificationData(comment=raw_data[0], classification=int(raw_data[1])))
        return results

    def preprocess_data(self, documents: List[str]):
        for comment in documents:
            if self.filters:
                for string in self.filters:
                    comment = comment.replace(string, "")
            yield self.regex.sub(' ', comment).lower().strip()

    def calculate_word_weights(self, documents: List[str], df, tf_mode: Mode):
        """Used to calculate word weights. tf_mode is the weighting scheme used on the frequency term.
        To use the raw word count, pass in 'count'.
        To use term frequency (raw count divided by words in document), pass in 'frequency'
        See: https://en.wikipedia.org/wiki/Tf%E2%80%93idf (tf weighting schemes: raw count, term frequency)"""
        tf = defaultdict(int)
        for comment in self.preprocess_data(documents):
            local_tf = defaultdict(int)
            words = comment.split()
            for word in words:
                if word:
                    self.vocabulary_frequency[word] += 1
                    local_tf[word] += 1
            if tf_mode is self.Mode.FREQ:
                num_words = len(words)
                local_tf = {k: v / num_words for k, v in local_tf.items()}
            for k, v in local_tf.items():
                tf[k] += v
                df[k] += 1
        return tf

    def apply_tf_idf(self, tf, num_docs):
        """See: https://en.wikipedia.org/wiki/Tf%E2%80%93idf (weighting scheme 1)"""
        for k, v in tf.items():
            idf = np.log(num_docs / self.document_frequency[k])
            tf[k] = v * idf

    def calculate_log_likelihood(self):
        num_words_in_vocabulary = len(self.vocabulary_frequency)
        for word in self.vocabulary_frequency:
            # todo: ensure denominator is correct
            # bayes_denominator = self.vocabulary_frequency[word] + self._ADD_ALPHA_SMOOTHING
            for cl in self.positive_class, self.negative_class:
                cl.log_likelihood[word] = np.log((cl.word_frequency[word] + self._ADD_ALPHA_SMOOTHING) /
                                                 (sum(cl.word_frequency.values()) + num_words_in_vocabulary))

    def train(self, data_list: List[ClassificationData], tf_mode: Mode = Mode.FREQ, tfidf=True):
        """tfidf specifies whether to weigh the words using term frequency - inverse document frequency algorithm"""
        positive_docs = [data.comment for data in data_list if data.classification == 1]
        negative_docs = [data.comment for data in data_list if data.classification == 0]
        num_docs = len(data_list)
        num_pos_docs = len(positive_docs)
        num_neg_docs = len(negative_docs)
        logger.info(
            f"Training data using {num_docs} total docs. {num_pos_docs} are positive, {num_neg_docs} are negative."
            f"Term frequency mode: {tf_mode}, tf-idf weighting is set to {tfidf}.")
        pos_freq = self.calculate_word_weights(positive_docs, self.document_frequency, tf_mode)
        neg_freq = self.calculate_word_weights(negative_docs, self.document_frequency, tf_mode)
        if tfidf:
            self.apply_tf_idf(pos_freq, num_docs)
            self.apply_tf_idf(neg_freq, num_docs)
        self.positive_class = DocumentClass(prior=num_pos_docs / num_docs, word_frequency=pos_freq)
        self.negative_class = DocumentClass(prior=num_neg_docs / num_docs, word_frequency=neg_freq)
        self.calculate_log_likelihood()
        logger.debug("Successfully trained classifier.")

    def test(self, documents):
        results = []
        logger.info(f"Testing {len(documents)} documents.")
        with futures.ThreadPoolExecutor() as executor:
            future_list = []
            for comment in self.preprocess_data(documents):
                future_list.append(executor.submit(self.classify_document, comment))
            for future in futures.as_completed(future_list):
                classification = future.result()
                results.append(classification)
        self.test_results = results
        logger.debug(f"Successfully classified Data.")
        return results

    def classify_document(self, comment):
        pos_log_likelihood = self.positive_class.prior
        neg_log_likelihood = self.negative_class.prior
        for word in comment.split():
            if word and word in self.vocabulary_frequency.keys():
                pos_log_likelihood += self.positive_class.log_likelihood[word]
                neg_log_likelihood += self.negative_class.log_likelihood[word]
        # if likelihoods are equal, consider it positive sentiment
        if pos_log_likelihood >= neg_log_likelihood:
            return ClassificationData(comment=comment, classification=1)
        else:
            return ClassificationData(comment=comment, classification=0)

    def convert_to_list(self) -> List[List]:
        results = []
        for result in self.test_results:
            results.append([result.comment, result.classification])
        return results
