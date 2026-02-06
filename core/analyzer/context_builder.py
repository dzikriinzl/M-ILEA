class ContextBuilder:
    def __init__(self, class_index):
        self.class_index = class_index

    def enrich_with_caller(self, sink_hit):
        # Optional: lightweight caller resolution
        callers = self.class_index.get_callers(
            sink_hit.class_name,
            sink_hit.method_name
        )
        if callers:
            sink_hit.caller = callers[0]
        return sink_hit
