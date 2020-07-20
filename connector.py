# Connector to bridge the MateCat API to the NECTM API: https://www.nec-tm.eu/
# MateCat API documentation: https://mymemory.translated.net/doc/spec.php
# NECTM documentation: - https://www.nec-tm.eu/wp-content/uploads/2020/03/NEC-TM-UI-description.pdf
#                     - https://www.nec-tm.eu/wp-content/uploads/2020/03/NEC-TM-Admin-UI-description.pdf
#                     - https://www.nec-tm.eu/wp-content/uploads/2020/03/NEC-TM-Technical-description.pdf
# NECTM source code :    https://github.com/Pangeamt/nectm/
from inflection import dasherize
import flask
from requests import post, get
from flask import request, jsonify
from flask.views import MethodView

HOST = 'http://nectm:7979'
USERNAME = 'admin'
PASSWORD = 'admin'

app = flask.Flask(__name__)


# access_token = post(f"{HOST}/api/v1/auth", json={'username': USERNAME,'password': PASSWORD}).json()['access_token']


class MatecatReponse:
    def __init__(self, quotaFinished=False, mtLangSupported=None, responseDetails="", responseStatus=200,
                 responderId='235', matches=[], exception_code=None):
        self.responseData = {'translatedText': '', 'match': 1}
        self.quotaFinished = quotaFinished
        self.mtLangSupported = mtLangSupported
        self.responseDetails = responseDetails
        self.responseStatus = responseStatus
        self.responderId = responderId
        self.matches = matches

    # method to convert the snake_case of instance variables to json standard of kebab-case expected by MateCat (kebab-case raises assign errors in Python)
    def getDict(self):
        dictionary = self.__dict__
        return dict([(dasherize(k), v)
                     for (k, v) in dictionary.items()])


class Match:
    def __init__(self, id, segment, translation, match, quality='75', reference='reference', subject='All',
                 usage_count=0, created_by='MateCat', last_updated_by='MateCat',
                 create_date='Tue Jul 07 11:47:11 GMT 2020', last_update_date='Tue Jul 07 11:47:11 GMT 2020'):
        self.id = id
        self.segment = segment
        self.translation = translation
        self.quality = quality
        self.reference = reference
        self.subject = subject
        self.match = match
        self.usage_count = usage_count
        self.created_by = created_by
        self.last_updated_by = last_updated_by
        self.create_date = create_date
        self.last_update_date = last_update_date

    # method to convert the snake_case of instance variables to json standard of kebab-case expected by MateCat (kebab-case raises assign errors in Python)
    def getDict(self):
        dictionary = self.__dict__
        return dict([(dasherize(k), v) for (k, v) in dictionary.items()])


class TmView(MethodView):
    def get(self):
        access_token = post(f"{HOST}/api/v1/auth", json={'username': USERNAME, 'password': PASSWORD}).json()[
            'access_token']
        data = request.get_json()
        q = data['q']
        langpair = data['langpair']
        if '|' in langpair:
            slang = langpair.split('|')[0].split('-')[0]
            tlang = langpair.split('|')[1].split('-')[0]
        else:
            slang = langpair.split('-')[0]
            tlang = langpair.split('-')[1]
        result_response = get(f"{HOST}/api/v1/tm",
                              headers={"Authorization": f"JWT {access_token}", "Content-Type": "application/json"},
                              json={"q": q, "slang": slang, "tlang": tlang})
        result_data = result_response.json()
        matches = []
        if len(result_data['results']):
            results = result_data['results']
            if not results[0]['tu']['source_text'] == " ":
                for result in results:
                    # sanity check
                    assert q == result['tu']['source_text']
                    match = Match(id=str(results.index(result)), segment=q, reference=q,
                                  translation=result['tu']['target_text'], match=float(result['match'] / 100)).getDict()
                    matches.append(match)
        return_blob = MatecatReponse(matches=matches)
        return return_blob.getDict()


tm_view = TmView.as_view('tm_api')
app.add_url_rule('/get/', methods=['GET'], view_func=tm_view)

if __name__ == "__main__":
    app.config["DEBUG"] = True
    app.run()
