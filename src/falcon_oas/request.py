import falcon


class Request(falcon.Request):
    @property
    def host_url(self):
        # type: (falcon.Request) -> Text
        return self.scheme + "://" + self.netloc

    @property
    def oas_query(self):
        # type: () -> Dict
        return self.context["oas.parameters"]["query"]

    @property
    def oas_header(self):
        # type: () -> Dict
        return self.context["oas.parameters"]["header"]

    @property
    def oas_cookie(self):
        # type: () -> Dict
        return self.context["oas.parameters"]["cookie"]

    @property
    def oas_media(self):
        # type: () -> Any
        return self.context["oas.request_body"]

    @property
    def oas_user(self):
        # type: () -> Any
        return self.context["oas.users"][0]

    @property
    def oas_users(self):
        # type: () -> List
        return self.context["oas.users"]
