import re

import apache_beam as beam

from analytic import core


class WordCountPipeline(core.Pipeline):

    def __init__(
            self,
            words_source: beam.PTransform,
            word_count_sink: beam.PTransform,
            output_format: str,
    ) -> None:
        self.words_source = words_source
        self.word_count_sink = word_count_sink
        self.output_format = output_format

    def define(self, pipeline: beam.Pipeline) -> None:
        def format_result(word, count):
            return self.output_format % (word, count)

        _ = (pipeline
             | 'Read' >> self.words_source
             | 'Split' >> (beam.ParDo(WordExtractingDoFn()).with_output_types(str))
             | 'PairWithOne' >> beam.Map(lambda x: (x, 1))
             | 'GroupAndSum' >> beam.CombinePerKey(sum)
             | 'Format' >> beam.MapTuple(format_result)
             | 'Write' >> self.word_count_sink)


class WordExtractingDoFn(beam.DoFn):

    def process(self, element, *args, **kwargs):
        return re.findall(r'[\w\']+', element, re.UNICODE)
