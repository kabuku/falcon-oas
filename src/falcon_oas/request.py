import falcon


class Request(falcon.Request):
    @property
    def oas_query(self):
        return self.context['oas'].parameters['query']

    @property
    def oas_header(self):
        return self.context['oas'].parameters['header']

    @property
    def oas_cookie(self):
        return self.context['oas'].parameters['cookie']

    @property
    def oas_media(self):
        return self.context['oas'].request_body

    @property
    def oas_user(self):
        return self.context['oas'].user
