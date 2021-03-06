import httplib2

from onadata.apps.restservice.RestServiceInterface import RestServiceInterface


class ServiceDefinition(RestServiceInterface):
    id = u'xml'
    verbose_name = u'XML POST'

    def send(self, url, submission_instance):
        headers = {"Content-Type": "application/xml"}
        http = httplib2.Http()
        resp, content = http.request(
            url, method="POST", body=submission_instance.xml, headers=headers)
