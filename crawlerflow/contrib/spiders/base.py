from scrapy.spiders import CrawlSpider
from crawlerflow.utils.spiders import get_spider_from_list
from crawlerflow.core.traversals.generic import GenericLinkExtractor
import scrapy
from scrapy.http import Request, FormRequest
from crawlerflow.utils.other import convert_dict_to_scrapy_headers
import logging

logger = logging.getLogger(__name__)


class CrawlerFlowSpiderBase(CrawlSpider):
    """

    TODO - document why we need this as base method.

    """

    # spider_id = None  # id of the current spider
    spider_config = None  # json config of the current crawler
    spider_data_storage = None  # TODO - we might not be using this anymore, remove with caution.
    manifest = {}
    current_request_traversal_id = None  # this will contain the config of traversal that led to this spider.

    def post_parse(self, response=None):
        pass

    def parse_error(self, failure):
        logger.error("failure : {}".format(failure))
        pass

    def get_spider_meta(self):
        return {
            "current_request_traversal_count": 0,
            "spider_config": self.spider_config,
            "manifest": self.manifest,
            "current_request_traversal_id": "init",
            "current_traversal_max_count": 1
        }

    def get_spider_request_kwargs(self):

        return {
            "errback": self.parse_error,
            "dont_filter": True,
            "meta": self.get_spider_meta()
        }

    """
    @staticmethod
    def get_headers_from_response_data(response):
        # works for scrapy response headers.
        all_headers = {}

        headers = response.headers
        # print("headersheadersheaders", type(headers), headers)
        cookies_temp = [cookie.decode().split(";")[0] for cookie in headers.getlist("Set-Cookie")]
        cookies = []
        for cookie in cookies_temp:
            _ = cookie.split("=")
            cookies.append({
                "name": _[0],
                "value": _[1]
            })

        all_headers['Cookies'] = cookies
        return all_headers    
    """

    @staticmethod
    def get_headers_from_response_data(response):
        all_headers = {}

        headers = response.headers
        print("<<<<<<<<headers", headers)
        # print("headersheadersheaders", type(headers), headers)
        cookies_temp = [cookie.decode().split(";")[0] for cookie in headers.getlist("Set-Cookie")]
        cookies = []
        for cookie in cookies_temp:
            _ = cookie.split("=")
            cookies.append({
                "name": _[0],
                "value": _[1]
            })

        all_headers['cookies'] = cookies
        return all_headers

    def _prepare_start_requests(self, urls=None, response=None):
        logger.info("Preparing start requests for urls: {}".format(urls))

        start_requests = []
        # headers = response.headers
        # print("headers", headers.getlist('Set-Cookie'))
        # cookies = {}
        # for cookie in response.headers.getlist('Set-Cookie'):
        #     single_cookie = str(cookie).split(';')[0].split("=")
        #     cookies[str(single_cookie[0]).lstrip("b'")] = single_cookie[1]
        # cookies['logged'] = True
        # print("cookies", cookies)
        # print("cookies", cookies.keys())
        # print(response.get_cookies())
        init_request_kwargs = self.get_spider_request_kwargs()
        if response:
            # all_headers = self.get_headers_from_response_data(response)
            all_headers = {"cookies": response.request.cookies}
        else:
            all_headers = {"cookies": []}

        logger.debug("all_headers {} {}".format(type(all_headers), all_headers))
        for url in urls:
            if response:
                requestKlass = response.follow
            else:
                requestKlass = scrapy.Request

            start_requests.append(requestKlass(
                url,
                callback=self.parse,
                cookies=response.request.cookies,
                # headers={'Cookie': cookie},
                # headers=convert_dict_to_scrapy_headers(all_headers),
                # headers=all_headers,
                # headers=response.headers,
                # cookies=cookies,
                **init_request_kwargs
            ))
        return start_requests

    #
    # def _prepare_login_request(self):
    #     """
    #     Generate a login parser request.
    #     """
    #     login_settings = self.spider_config.get("login_settings", None)
    #     if login_settings:
    #         login_request_kwargs = {}
    #         form_identifiers = login_settings.get("form_identifiers", {})
    #         auth_type = login_settings.get("auth_type", "cookies")
    #         if auth_type == "cookies":
    #             form_kwargs = {
    #                 "formdata": {
    #                     form_identifiers['username_field']: login_settings['username'],
    #                     form_identifiers['password_field']: login_settings['password']
    #                 },
    #                 "formcss": form_identifiers['form_selector'],
    #                 "formnumber": form_identifiers.get('formnumber', 0)
    #             }
    #             login_request_kwargs.update(form_kwargs)
    #         else:
    #             raise NotImplementedError("only auth_type=cookies is supported currently.")
    #         return login_request_kwargs
    #     else:
    #         return None

    def _prepare_login_request(self):
        """
        Generate a login parser request.
        """
        login_settings = self.spider_config.get("login_settings", None)
        if login_settings:
            login_request_kwargs = {}
            form_settings = login_settings.get("form_settings", {})

            form_identifiers = login_settings.get("form_identifiers", {})
            auth_type = login_settings.get("auth_type", "cookies")
            if auth_type == "cookies":
                form_kwargs = {
                    "formdata": {
                        form_identifiers['username_field']: login_settings['username'],
                        form_identifiers['password_field']: login_settings['password']
                    },
                    "formcss": form_identifiers['form_selector'],
                    "formnumber": form_identifiers.get('formnumber', 0)
                }
                login_request_kwargs.update(form_kwargs)
            else:
                raise NotImplementedError("only auth_type=cookies is supported currently.")
            return login_request_kwargs
        else:
            return None

    def login_request(self):
        """This function is called before crawling starts."""
        login_settings = self.spider_config.get("login_settings", {})
        login_url = login_settings.get("url")
        init_request_kwargs = self.get_spider_request_kwargs()
        init_request_kwargs['meta']['is_login_request'] = True
        # init_request_kwargs['meta']['dont_redirect'] = True
        # init_request_kwargs['meta']['handle_httpstatus_list'] = [302, ]
        # return Request(url=login_url, **init_request_kwargs, callback=self.login_parser, )
        return Request(url=login_url, **init_request_kwargs, callback=self.post_login_init_parser, )

    # def login_parser(self, response):
    #     login_request_kwargs = self._prepare_login_request()
    #     request_kwargs = self.get_spider_request_kwargs()
    #     # del login_request_kwargs['formcss']
    #     # login_request_kwargs['formid'] = "new_user"
    #     login_request_kwargs['method'] = "post"
    #     request_kwargs['meta'].update(
    #         {'dont_redirect': True, "handle_httpstatus_list": [302], 'is_login_request': True}
    #         # {'is_login_request': True}
    #     )
    #     return FormRequest.from_response(
    #         response,
    #         **login_request_kwargs,
    #         **request_kwargs,
    #         # method="POST",
    #         callback=self.post_login_init_parser,
    #     )

    def post_login_init_parser(self, response):
        is_login_request = response.request.meta.get("is_login_request")
        if is_login_request:
            validation_string = self.spider_config.get("login_settings", {}).get("validation_string")
            logger.debug("====response status {}".format(response.status))
            logger.debug("====response body {}".format(response.body))
            if validation_string in str(response.body or ''):
                logger.info("<<<< LOGIN SUCCESSFUL >>>> with headers {}".format(response.headers))
            else:
                logger.info("<<<< LOGIN FAILED >>>>>")

        start_requests = self._prepare_start_requests(urls=self.start_urls, response=response)
        logger.debug("start_requests ::{}".format(start_requests))
        for request in start_requests:
            yield request

    def start_requests(self):
        login_settings = self.spider_config.get("login_settings", {})
        login_url = login_settings.get("url")
        if login_url:
            yield self.login_request()
        else:
            start_requests = self._prepare_start_requests(urls=self.start_urls)
            for request in start_requests:
                yield request

    def get_spider_config(self, response=None):
        if response.meta.get("spider_config"):
            return response.meta.get("spider_config")
        else:
            return self.spider_config

    @staticmethod
    def get_default_storage(settings=None, spider_config=None):
        data_storages = settings.get("DATA_STORAGES", [])
        default_storage = None
        spider_storage_id = "default"
        for data_storage in data_storages:
            __storage_id = data_storage.get("storage_id") or data_storage.get("STORAGE_ID")
            if __storage_id == spider_storage_id:
                return data_storage
        return default_storage

    @staticmethod
    def prepare_data_for_yield(data=None, collection_name=None, storage_id="default"):
        return {
            "_data_storage_id": storage_id,
            "_data": data
        }

    @staticmethod
    def is_this_request_from_same_traversal(response, traversal):
        """
        This mean the current request came from this  traversal,
        so we can put max pages condition on this, otherwise for different
        traversals of different spiders, adding max_page doest make sense.
        """
        traversal_id = traversal['traversal_id']
        current_request_traversal_id = response.meta.get('current_request_traversal_id', None)
        return current_request_traversal_id == traversal_id

    def make_traversal_requests(self, to_traverse_links_list=None, response=None):
        traversal_requests = []
        for to_traverse_link in to_traverse_links_list:
            traversal_requests.append(response.follow(
                to_traverse_link.get("link"),
                callback=self.parse,
                errback=self.parse_error,
                cookies=response.request.cookies,
                headers=response.headers,
                meta=to_traverse_link.get("meta", {})
            ))
        return traversal_requests

    @staticmethod
    def run_traversal(response=None, traversal=None, **kwargs):

        selector_type = traversal.get("selector_type", "css")
        kwargs = {}
        if selector_type == "css":
            kwargs['restrict_css'] = (traversal.get("selector_value"),)
        elif selector_type == "xpath":
            kwargs['restrict_xpaths'] = (traversal.get("selector_value"),)

        kwargs['allow_domains'] = traversal.get("allow_domains", [])
        return GenericLinkExtractor(**kwargs).extract_links(response=response)

    @staticmethod
    def get_traversal_max_pages(traversal=None):
        return traversal.get('max_pages', 1)

    def get_current_traversal_requests_count(self, traversal_id=None):
        return self.crawler.stats.get_value(
            'crawlerflow-stats/traversals/{}/requests_count'.format(traversal_id)) or 0

    def run_traversals(self, spider_config=None, response=None):
        """
        if spider_traversal_id is None, it means this response originated from the
        request raised by the start urls.

        If it is Not None, the request/response is raised some traversal strategy.
        """
        current_request_traversal_id = response.meta.get('current_request_traversal_id', None)

        """
        Note on current_request_spider_id:
        This can never be none, including the ones that are started by start_urls .
        """
        traversal_data = {}
        to_traverse_links_list = []
        spider_traversals = spider_config.get('traversals', [])
        spiders = response.meta.get("manifest", {}).get("spiders")

        for traversal in spider_traversals:
            next_spider_id = traversal['next_spider_id']
            next_spider = get_spider_from_list(spider_id=next_spider_id, spiders=spiders)

            traversal['allow_domains'] = next_spider.get("spider_settings", {}).get("allowed_domains", [])
            traversal_id = traversal['traversal_id']
            current_request_traversal_count = self.get_current_traversal_requests_count(traversal_id)
            traversal_max_pages = self.get_traversal_max_pages(traversal=traversal)
            traversal_links = []
            is_this_request_from_same_traversal = self.is_this_request_from_same_traversal(response, traversal)
            shall_traverse = False

            if current_request_traversal_id is None:
                """
                start urls will not have this traversal_id set, so we should allow then to traverse
                """
                shall_traverse = True

            elif is_this_request_from_same_traversal and current_request_traversal_count < traversal_max_pages:
                """
                This block will be valid for the traversals from same spider_id, ie., pagination of a spider 
                """

                shall_traverse = True

            elif is_this_request_from_same_traversal:
                """
                """
                shall_traverse = True

            elif is_this_request_from_same_traversal is False and current_request_traversal_count < traversal_max_pages:
                """
                This for the spider_a traversing to spider_b, this is not pagination, but trsversing between 
                spiders.
                """
                shall_traverse = True

            if shall_traverse:
                traversal_links = self.run_traversal(response=response, traversal=traversal)
                traversal_data[traversal_id] = {"traversal_urls": traversal_links}
                """
                Then validate for max_pages logic if traversal_id's traversal has any!.
                This is where the further traversal for this traversal_id  is decided 
                """
                max_pages = self.get_traversal_max_pages(traversal=traversal)

                for link in traversal_links:

                    """
                    we are already incrementing, the last number, so using <= might make it 6 pages when 
                    max_pages is 5 
                    """
                    if current_request_traversal_count < max_pages:
                        to_traverse_links_list.append(
                            {
                                "link": link,
                                "meta": {
                                    "spider_config": next_spider,
                                    "manifest": response.meta.get("manifest"),
                                    "current_request_traversal_id": traversal_id,
                                    "current_request_traversal_count": current_request_traversal_count,
                                    "current_traversal_max_count": max_pages,

                                }}
                        )

                    current_request_traversal_count += 1

            logger.info("Extracted {} traversal_links for traversal_id:'{}' in url:{}".format(len(traversal_links),
                                                                                              traversal_id,
                                                                                              response.url))
        return traversal_data, to_traverse_links_list

    # def login_request(self):
