class ValidRequest:
    def __init__(self, required_args=None, optional_args=None):
        self.required_args = required_args
        self.optional_args = optional_args
        self.args = {}
        self.missing = []

    def parse(self, r):
        if self.required_args:
            for arg in self.required_args:
                value = r.args.get(arg)
                if not value:
                    print("Missing req: {}".format(arg))
                    return False
                else:
                    self.args[arg] = value

        if self.optional_args:
            for arg in self.optional_args:
                value = r.args.get(arg)
                if not value:
                    self.missing.append(arg)
                else:
                    self.args[arg] = value
        return True

    def get(self, arg):
        return self.args[arg]