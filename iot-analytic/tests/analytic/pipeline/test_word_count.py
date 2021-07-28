from analytic.pipeline.word_count import WordCountPipeline


def test_pipeline(helpers):
    pipeline = WordCountPipeline(
            helpers.resource_as_pcollection(__file__, 'data/words_source.json'),
            helpers.resource_as_assert_pcollection(__file__, 'data/word_count_sink.json'),
            '%s - %s')

    helpers.assert_pipeline(pipeline)
