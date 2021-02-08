from classifier.naive_bayes import NaiveBayes


def test_naive_bayes_classifies_correctly(classification_data):
    ticker, training_data, test_data, expected_output, list_output = classification_data
    naive_bayes = NaiveBayes(words_to_ignore=[ticker])
    naive_bayes.train(training_data)
    actual_output = naive_bayes.test(test_data)
    actual_list_output = naive_bayes.convert_to_list()
    # convert to frozenset so assertion order does not matter (since we use concurrency)
    assert {frozenset(item) for item in actual_output} == {frozenset(item) for item in expected_output}
    assert sorted(actual_list_output) == sorted(list_output)
